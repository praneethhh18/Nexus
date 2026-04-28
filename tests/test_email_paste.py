"""
Email-paste lead capture — contract tests.

LLM is mocked. Tests cover:
  - extract_email returns the parsed JSON shape; UI uses these fields directly
  - garbage LLM output → regex-fallback (sender from "From:" header)
  - dedup on email creates an interaction on the existing contact, no new row
  - save_from_email persists with source='email_paste'
  - cross-tenant safety: user A can't write to user B's workspace via this path
  - sensitive=True is set on the LLM call (privacy invariant)
  - bad inputs (no name, no email) → 400
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest
from fastapi import HTTPException


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    from api.routers import lead_scoring as _ls
    importlib.reload(_ls)
    from api.routers import email_paste as _ep
    importlib.reload(_ep)
    return _crm, _ep


def _ctx(business_id, role="admin"):
    return {
        "user": {"id": "u-test", "name": "Test"},
        "business_id": business_id,
        "business_role": role,
    }


SAMPLE_EMAIL = """\
From: Priya Sharma <priya@acme.com>
Subject: Interested in your product
Date: Mon, 4 May 2026

Hi there,

We're a 200-person SaaS company looking for a privacy-first CRM.
Could we hop on a 15-minute call this week?

Thanks,
Priya
Head of Sales, Acme Inc.
"""


# ── Extraction (preview path) ───────────────────────────────────────────────
def test_extract_returns_parsed_fields():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ep = _fresh(db)

        canned = (
            '{"sender_name": "Priya Sharma", "sender_email": "priya@acme.com", '
            '"sender_company": "Acme Inc.", "subject": "Interested in your product", '
            '"summary": "200-person SaaS wants a privacy-first CRM, asks for a 15-min call."}'
        )
        from api.routers.email_paste import EmailPasteIn
        with patch("api.routers.email_paste.llm_invoke", return_value=canned) as mocked:
            r = ep.extract_email(EmailPasteIn(raw_email=SAMPLE_EMAIL), ctx=_ctx("biz-a"))

        assert r["sender_name"] == "Priya Sharma"
        assert r["sender_email"] == "priya@acme.com"
        assert r["sender_company"] == "Acme Inc."
        assert r["subject"].startswith("Interested")
        assert "SaaS" in r["summary"]
        assert r["fallback"] is False
        # Privacy invariant — extraction sees full email body.
        assert mocked.call_args.kwargs.get("sensitive") is True


def test_extract_falls_back_to_regex_on_garbage():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ep = _fresh(db)

        from api.routers.email_paste import EmailPasteIn
        with patch("api.routers.email_paste.llm_invoke", return_value="hmm not sure"):
            r = ep.extract_email(EmailPasteIn(raw_email=SAMPLE_EMAIL), ctx=_ctx("biz-a"))

        # The regex fallback at least pulls the From: header.
        assert r["fallback"] is True
        assert r["sender_email"] == "priya@acme.com"
        assert r["sender_name"] == "Priya Sharma"


def test_extract_handles_llm_unreachable():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ep = _fresh(db)
        from api.routers.email_paste import EmailPasteIn
        with patch("api.routers.email_paste.llm_invoke", side_effect=Exception("Ollama offline")):
            r = ep.extract_email(EmailPasteIn(raw_email=SAMPLE_EMAIL), ctx=_ctx("biz-a"))
        # Degrades to regex fallback rather than 5xx-ing — UI stays usable.
        assert r["fallback"] is True
        assert r["sender_email"] == "priya@acme.com"


# ── Save path ───────────────────────────────────────────────────────────────
def test_save_creates_contact_with_email_paste_source():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ep = _fresh(db)

        from api.routers.email_paste import EmailPasteSaveIn
        r = ep.save_from_email(EmailPasteSaveIn(
            raw_email=SAMPLE_EMAIL,
            sender_name="Priya Sharma",
            sender_email="priya@acme.com",
            sender_company="Acme Inc.",
            subject="Interested in your product",
            summary="Wants a CRM call.",
        ), ctx=_ctx("biz-a"))

        assert r["ok"] is True
        assert r["deduped"] is False
        contacts = crm.list_contacts("biz-a", limit=50)
        match = [c for c in contacts if (c.get("email") or "").lower() == "priya@acme.com"]
        assert len(match) == 1, f"Contact not landed: {contacts}"

        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT source FROM nexus_contacts WHERE id = ?", (match[0]["id"],),
            ).fetchone()
            assert row[0] == "email_paste"
        finally:
            conn.close()

        # Interaction was logged.
        ints = crm.list_interactions("biz-a", contact_id=match[0]["id"], limit=10)
        assert len(ints) >= 1
        assert ints[0]["type"] == "email"


def test_save_dedups_on_email():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ep = _fresh(db)

        # First save creates the contact.
        from api.routers.email_paste import EmailPasteSaveIn
        ep.save_from_email(EmailPasteSaveIn(
            raw_email=SAMPLE_EMAIL,
            sender_name="Priya", sender_email="priya@acme.com",
        ), ctx=_ctx("biz-a"))

        # Second save (later forwarded email from same person) must dedup.
        r = ep.save_from_email(EmailPasteSaveIn(
            raw_email="From: priya@acme.com\nSubject: Re: pilot",
            sender_name="Priya Sharma", sender_email="priya@acme.com",
            summary="Following up",
        ), ctx=_ctx("biz-a"))
        assert r["deduped"] is True

        # Still one contact, but two interactions logged.
        contacts = [c for c in crm.list_contacts("biz-a", limit=50)
                    if (c.get("email") or "").lower() == "priya@acme.com"]
        assert len(contacts) == 1
        ints = crm.list_interactions("biz-a", contact_id=contacts[0]["id"], limit=10)
        assert len(ints) == 2


def test_save_rejects_when_no_name_or_email():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ep = _fresh(db)

        from api.routers.email_paste import EmailPasteSaveIn
        with pytest.raises(HTTPException) as exc:
            ep.save_from_email(EmailPasteSaveIn(
                raw_email="some pasted text without sender info" * 2,
                sender_name="", sender_email="",
            ), ctx=_ctx("biz-a"))
        assert exc.value.status_code == 400


def test_save_isolates_per_tenant():
    """A captured email lands in the calling user's workspace, not anywhere else."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ep = _fresh(db)

        from api.routers.email_paste import EmailPasteSaveIn
        ep.save_from_email(EmailPasteSaveIn(
            raw_email=SAMPLE_EMAIL,
            sender_name="Priya Sharma", sender_email="priya@acme.com",
        ), ctx=_ctx("biz-a"))

        biz_b_contacts = crm.list_contacts("biz-b", limit=50)
        assert all((c.get("email") or "").lower() != "priya@acme.com" for c in biz_b_contacts), (
            "Contact must NOT have leaked to biz-b"
        )
