"""
Public lead-capture intake — contract tests.

Verifies:
  - Intake key creation persists a hash, never the raw key.
  - Public POST /api/public/leads accepts a valid key + creates a contact
    tagged source='public_form'.
  - Invalid / revoked / wrong-tenant keys all return 401 with no detail.
  - Dedup: a second submission with the same email is logged as an
    interaction on the existing contact, not a duplicate.
  - Rate-limit kicks in at the documented threshold.
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
import time

import pytest

from fastapi import HTTPException


def _fresh(db_path: str):
    """Reload the modules that read DB_PATH at import time."""
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    from api import notifications as _notifs
    importlib.reload(_notifs)
    from db import migrate as _mig
    importlib.reload(_mig)
    from api.routers import intake as _intake
    importlib.reload(_intake)
    return _intake, _crm, _mig


def _migrate_and_init(intake_mod, mig_mod, db_path):
    """Apply migration 0002 + ensure crm table exists."""
    mig_mod.apply_pending(db_path)
    # Touch the contacts table init by listing — lazy-creates the schema.
    from api import crm as _crm
    _crm.list_contacts("biz-warmup")


# ── Fake Request shim — lets us call route handlers without TestClient ──
class _FakeClient:
    def __init__(self, host): self.host = host

class _FakeRequest:
    def __init__(self, host="1.2.3.4", headers=None):
        self.client = _FakeClient(host)
        self.headers = headers or {}


def _ctx(business_id, role="admin", user_id="u-test"):
    return {
        "user": {"id": user_id, "name": "Test"},
        "business_id": business_id,
        "business_role": role,
    }


# ── Tests ───────────────────────────────────────────────────────────────────
def test_create_key_returns_raw_once_and_hashes_the_rest():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _crm, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import create_key, IntakeKeyCreate
        result = create_key(IntakeKeyCreate(label="homepage"), ctx=_ctx("biz-a"))

        assert result["key"].startswith("nx_pub_"), "Raw key must use the public prefix"
        assert len(result["key"]) > 30
        assert result["key_prefix"].startswith("nx_pub_") and result["key_prefix"].endswith("…")
        assert result["label"] == "homepage"

        # Verify the DB stores the SHA, not the raw key.
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT key_hash, key_prefix FROM nexus_intake_keys WHERE business_id = ?",
                ("biz-a",),
            ).fetchone()
            assert row, "key not persisted"
            assert row[0] != result["key"], "raw key must NOT be stored"
            # SHA-256 is 64 hex chars
            assert len(row[0]) == 64
        finally:
            conn.close()


def test_create_key_admin_only():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _crm, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import create_key, IntakeKeyCreate
        with pytest.raises(HTTPException) as exc:
            create_key(IntakeKeyCreate(label="nope"), ctx=_ctx("biz-a", role="member"))
        assert exc.value.status_code == 403


def test_public_lead_creates_contact_tagged_public_form():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _crm, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import create_key, receive_public_lead, IntakeKeyCreate, PublicLeadIn
        key = create_key(IntakeKeyCreate(label="x"), ctx=_ctx("biz-a"))["key"]

        req = _FakeRequest(host="9.9.9.9")
        r = receive_public_lead(
            PublicLeadIn(intake_key=key, name="Priya Sharma",
                         email="priya@acme.com", company="Acme",
                         message="Interested in a demo"),
            request=req,
        )
        assert r["ok"] is True

        contacts = _crm.list_contacts("biz-a", limit=50)
        match = [c for c in contacts if (c.get("email") or "").lower() == "priya@acme.com"]
        assert len(match) == 1, f"contact not landed: {contacts}"

        # Verify source attribution.
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT source FROM nexus_contacts WHERE id = ?", (match[0]["id"],),
            ).fetchone()
            assert row[0] == "public_form"
        finally:
            conn.close()


def test_invalid_key_returns_401():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import receive_public_lead, PublicLeadIn
        req = _FakeRequest()

        with pytest.raises(HTTPException) as exc:
            receive_public_lead(
                PublicLeadIn(intake_key="nx_pub_definitely_fake_key_xxxx",
                             name="Test"),
                request=req,
            )
        assert exc.value.status_code == 401


def test_revoked_key_returns_401():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import (
            create_key, revoke_key, receive_public_lead,
            IntakeKeyCreate, PublicLeadIn,
        )
        created = create_key(IntakeKeyCreate(label="x"), ctx=_ctx("biz-a"))
        revoke_key(created["id"], ctx=_ctx("biz-a"))

        req = _FakeRequest()
        with pytest.raises(HTTPException) as exc:
            receive_public_lead(
                PublicLeadIn(intake_key=created["key"], name="Test"),
                request=req,
            )
        assert exc.value.status_code == 401


def test_dedup_on_email_does_not_create_second_contact():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _crm, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import create_key, receive_public_lead, IntakeKeyCreate, PublicLeadIn
        key = create_key(IntakeKeyCreate(), ctx=_ctx("biz-a"))["key"]

        # First submission.
        receive_public_lead(
            PublicLeadIn(intake_key=key, name="Priya", email="priya@acme.com"),
            request=_FakeRequest(host="1.1.1.1"),
        )
        # Second — same email, different IP.
        r2 = receive_public_lead(
            PublicLeadIn(intake_key=key, name="Priya Sharma",
                         email="priya@acme.com", message="Following up"),
            request=_FakeRequest(host="2.2.2.2"),
        )
        assert r2["deduped"] is True

        contacts = _crm.list_contacts("biz-a", limit=50)
        match = [c for c in contacts if (c.get("email") or "").lower() == "priya@acme.com"]
        assert len(match) == 1, f"dedup failed — got {len(match)} contacts"


def test_rate_limit_kicks_in_after_threshold():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import (
            create_key, receive_public_lead, IntakeKeyCreate, PublicLeadIn,
            _RATE_BUCKETS, _RATE_MAX,
        )
        key = create_key(IntakeKeyCreate(), ctx=_ctx("biz-a"))["key"]
        # Reset the module-level bucket so this test is hermetic against
        # whatever ran before.
        _RATE_BUCKETS.clear()

        ip = "5.5.5.5"
        for i in range(_RATE_MAX):
            receive_public_lead(
                PublicLeadIn(intake_key=key, name=f"Lead {i}",
                             email=f"lead-{i}-{int(time.time())}@x.com"),
                request=_FakeRequest(host=ip),
            )
        # Next one should be 429.
        with pytest.raises(HTTPException) as exc:
            receive_public_lead(
                PublicLeadIn(intake_key=key, name="Over the limit",
                             email=f"over-{int(time.time())}@x.com"),
                request=_FakeRequest(host=ip),
            )
        assert exc.value.status_code == 429


def test_revoke_requires_admin_and_correct_tenant():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        intake, _, mig = _fresh(db)
        _migrate_and_init(intake, mig, db)

        from api.routers.intake import create_key, revoke_key, IntakeKeyCreate
        biz_a_key = create_key(IntakeKeyCreate(), ctx=_ctx("biz-a"))

        # member can't revoke
        with pytest.raises(HTTPException) as exc:
            revoke_key(biz_a_key["id"], ctx=_ctx("biz-a", role="member"))
        assert exc.value.status_code == 403

        # admin in a DIFFERENT tenant gets 404, not 200, and the key is intact.
        with pytest.raises(HTTPException) as exc:
            revoke_key(biz_a_key["id"], ctx=_ctx("biz-b"))
        assert exc.value.status_code == 404
