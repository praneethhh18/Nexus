"""
Sample-data seeder — smoke test.

Coverage:
  - Idempotent: refuses to seed a business that already has CRM data.
  - Happy path: companies/contacts/deals/tasks/invoices land, plus the
    AI-feature extras (ICP, intake key, lead scores, BANT, source tags,
    Forge "(unknown)" contact, follow-up-triggering stale interaction).
"""
from __future__ import annotations

import importlib
import json
import os
import sqlite3
import tempfile
from datetime import datetime, timezone


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    from api import seed_data as _sd
    importlib.reload(_sd)
    return _sd, _crm


def test_seed_creates_full_demo_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sd, crm = _fresh(db)

        result = sd.seed_sample_data("biz-demo", "u-test")
        assert result["seeded"] is True
        c = result["counts"]
        # Original counts.
        assert c["companies"] == 4
        assert c["deals"] == 5
        # Forge "(unknown)" contact pushes total above the base 5.
        assert c["contacts"] >= 6
        assert c["interactions"] >= 5
        assert c["icp"] == 1
        assert c["intake_keys"] == 1

        # ICP description landed.
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT icp_description FROM nexus_workspace_settings WHERE business_id = ?",
                ("biz-demo",),
            ).fetchone()
            assert row is not None and row[0]
            assert "ICP" not in row[0]  # we wrote prose, not the literal acronym

            # Intake key landed (key_hash present, prefix visible).
            keys = conn.execute(
                "SELECT key_prefix FROM nexus_intake_keys WHERE business_id = ?",
                ("biz-demo",),
            ).fetchall()
            assert len(keys) == 1
            assert keys[0][0].endswith("…")

            # Lead scores landed on at least one contact.
            scored = conn.execute(
                "SELECT COUNT(*) FROM nexus_contacts WHERE business_id = ? AND lead_score IS NOT NULL",
                ("biz-demo",),
            ).fetchone()[0]
            assert scored >= 3

            # BANT JSON landed on the negotiation-stage contact.
            bant = conn.execute(
                "SELECT bant_signals FROM nexus_contacts WHERE business_id = ? AND bant_signals != '' AND bant_signals IS NOT NULL",
                ("biz-demo",),
            ).fetchone()
            assert bant is not None
            parsed = json.loads(bant[0])
            assert parsed["budget"]["signal"] == "yes"
            assert parsed["suggested_stage"] == "negotiation"

            # Source variety: at least 3 distinct source labels.
            sources = {r[0] for r in conn.execute(
                "SELECT DISTINCT source FROM nexus_contacts WHERE business_id = ?",
                ("biz-demo",),
            ).fetchall()}
            # ai_outbound proves the Forge candidate landed too.
            assert "ai_outbound" in sources
            assert len(sources) >= 3

            # Forge "(unknown)" contact present so the verify banner shows.
            unknown = conn.execute(
                "SELECT COUNT(*) FROM nexus_contacts WHERE business_id = ? AND first_name = '(unknown)'",
                ("biz-demo",),
            ).fetchone()[0]
            assert unknown == 1
        finally:
            conn.close()

        # Stale interaction for follow-up nudge: at least one interaction
        # is more than 7 days old.
        ints = crm.list_interactions("biz-demo", limit=100)
        now = datetime.now(timezone.utc)
        old_count = 0
        for it in ints:
            ts = it.get("occurred_at") or it.get("created_at")
            if not ts:
                continue
            try:
                dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            except Exception:
                continue
            if (now - dt).days >= 7:
                old_count += 1
        assert old_count >= 1


def test_seed_is_idempotent():
    """Re-running on a populated business returns seeded=False."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        sd, _crm = _fresh(db)

        first = sd.seed_sample_data("biz-demo", "u-test")
        assert first["seeded"] is True

        second = sd.seed_sample_data("biz-demo", "u-test")
        assert second["seeded"] is False
        assert "already has" in second["reason"].lower()
