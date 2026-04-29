"""
BANT extraction — contract tests.

LLM is mocked. Coverage:
  - parser handles documented JSON shape
  - parser normalises sloppy input (e.g. "yes" vs {"signal": "yes"})
  - confidence is clamped 0..100
  - invalid stage suggestions become null
  - garbage output → safe empty state, no fabrication
  - persists to nexus_contacts.bant_signals
  - prompt runs sensitive=True (privacy invariant)
  - cross-tenant blocked
"""
from __future__ import annotations

import importlib
import json
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
    from api.routers import bant as _bant
    importlib.reload(_bant)
    return _crm, _bant


def _ctx(business_id, role="admin"):
    return {"user": {"id": "u-test", "name": "T"}, "business_id": business_id,
            "business_role": role}


# ── Parser ──────────────────────────────────────────────────────────────────
def test_parser_handles_clean_json():
    from api.routers.bant import _parse_bant
    raw = json.dumps({
        "budget":    {"signal": "yes",     "evidence": "approved budget Q2"},
        "authority": {"signal": "yes",     "evidence": "I make the decision"},
        "need":      {"signal": "unknown", "evidence": "none"},
        "timing":    {"signal": "yes",     "evidence": "want to start in 30 days"},
        "confidence": 75,
        "suggested_stage": "qualified",
        "summary": "Strong qualified lead",
    })
    out = _parse_bant(raw)
    assert out["budget"]["signal"] == "yes"
    assert out["confidence"] == 75
    assert out["suggested_stage"] == "qualified"


def test_parser_normalises_sloppy_signal_strings():
    """If the LLM returns just a string like 'yes' instead of an object,
    coerce it without erroring."""
    from api.routers.bant import _parse_bant
    raw = '{"budget": "yes", "authority": "no", "need": "unknown", "timing": "unknown", "confidence": 40}'
    out = _parse_bant(raw)
    assert out["budget"] == {"signal": "yes", "evidence": ""}
    assert out["authority"] == {"signal": "no",  "evidence": ""}


def test_parser_clamps_confidence():
    from api.routers.bant import _parse_bant
    out = _parse_bant('{"budget": {"signal":"yes"}, "authority":{"signal":"yes"}, "need":{"signal":"yes"}, "timing":{"signal":"yes"}, "confidence": 9999}')
    assert out["confidence"] == 100
    out = _parse_bant('{"budget": {"signal":"yes"}, "authority":{"signal":"yes"}, "need":{"signal":"yes"}, "timing":{"signal":"yes"}, "confidence": -50}')
    assert out["confidence"] == 0


def test_parser_rejects_invalid_stage():
    from api.routers.bant import _parse_bant
    out = _parse_bant('{"budget":{"signal":"yes"},"authority":{"signal":"yes"},"need":{"signal":"yes"},"timing":{"signal":"yes"},"confidence":80,"suggested_stage":"some_made_up_stage"}')
    assert out["suggested_stage"] is None


def test_parser_returns_none_on_garbage():
    from api.routers.bant import _parse_bant
    assert _parse_bant("the model rambled") is None
    assert _parse_bant("") is None


# ── End-to-end ──────────────────────────────────────────────────────────────
def test_extract_persists_and_returns_bant():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, bant = _fresh(db)
        c = crm.create_contact("biz-a", "u", {"first_name": "Priya"})

        canned = json.dumps({
            "budget":    {"signal": "yes", "evidence": "got Q2 budget"},
            "authority": {"signal": "yes", "evidence": "head of sales"},
            "need":      {"signal": "yes", "evidence": "current tool too expensive"},
            "timing":    {"signal": "no",  "evidence": "decision in Q4 next year"},
            "confidence": 65,
            "suggested_stage": "qualified",
            "summary": "Strong on B/A/N, slow on T",
        })

        from api.routers.bant import BantExtractIn
        with patch("api.routers.bant.llm_invoke", return_value=canned) as mocked:
            result = bant.extract_bant_api(
                contact_id=c["id"],
                payload=BantExtractIn(reply_text="Hi, we have budget approved for Q2..."),
                ctx=_ctx("biz-a"),
            )

        # sensitive=True is mandatory — the prompt sees customer reply text.
        assert mocked.call_args.kwargs.get("sensitive") is True
        assert result["budget"]["signal"] == "yes"
        assert result["suggested_stage"] == "qualified"

        # Verify persistence on the contact row.
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT bant_signals, bant_extracted_at FROM nexus_contacts WHERE id = ?",
                (c["id"],),
            ).fetchone()
            assert row[0]
            stored = json.loads(row[0])
            assert stored["confidence"] == 65
            assert row[1]  # extracted_at
        finally:
            conn.close()


def test_extract_safe_empty_state_on_garbage_llm():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, bant = _fresh(db)
        c = crm.create_contact("biz-a", "u", {"first_name": "Test"})

        from api.routers.bant import BantExtractIn
        with patch("api.routers.bant.llm_invoke", return_value="meh, hard to tell"):
            result = bant.extract_bant_api(
                contact_id=c["id"],
                payload=BantExtractIn(reply_text="Some reply text that's long enough"),
                ctx=_ctx("biz-a"),
            )

        # All four signals should be "unknown" — never invent a "yes".
        for k in ("budget", "authority", "need", "timing"):
            assert result[k]["signal"] == "unknown"
        assert result["confidence"] == 0
        assert result["suggested_stage"] is None


def test_extract_404s_on_cross_tenant_contact():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, bant = _fresh(db)
        biz_b = crm.create_contact("biz-b", "u", {"first_name": "BobB"})

        from api.routers.bant import BantExtractIn
        with pytest.raises(HTTPException) as exc:
            bant.extract_bant_api(
                contact_id=biz_b["id"],
                payload=BantExtractIn(reply_text="some reply text long enough"),
                ctx=_ctx("biz-a"),
            )
        assert exc.value.status_code == 404
