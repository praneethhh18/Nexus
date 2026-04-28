"""
AI lead scoring — contract tests.

The LLM is mocked. Tests cover:
  - parser handles JSON-only output, JSON-in-prose, and garbage
  - score is clamped to 0-100
  - bucket boundaries: 80=high, 50=medium, 20=low, 0=spam
  - scoring without an ICP is a no-op (returns null + actionable reason)
  - scoring persists score + reason + scored_at to nexus_contacts
  - cross-tenant scoring is rejected (404)
  - ICP write requires admin/owner; member is rejected (403)
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
    return _crm, _ls


def _ctx(business_id, role="admin"):
    return {
        "user": {"id": "u-test", "name": "Test"},
        "business_id": business_id,
        "business_role": role,
    }


# ── Parser ──────────────────────────────────────────────────────────────────
def test_parser_handles_clean_json():
    from api.routers.lead_scoring import _parse_score
    result = _parse_score('{"score": 85, "reason": "Strong B2B SaaS match"}')
    assert result == {"score": 85, "reason": "Strong B2B SaaS match"}


def test_parser_extracts_json_from_prose():
    """Some local models prepend explanation text. Should still extract JSON."""
    from api.routers.lead_scoring import _parse_score
    result = _parse_score(
        'Here is my analysis:\n{"score": 60, "reason": "Mid-market fit"}\nDone.'
    )
    assert result["score"] == 60


def test_parser_clamps_score_to_range():
    from api.routers.lead_scoring import _parse_score
    assert _parse_score('{"score": 150, "reason": "x"}')["score"] == 100
    assert _parse_score('{"score": -20, "reason": "x"}')["score"] == 0


def test_parser_returns_none_on_garbage():
    from api.routers.lead_scoring import _parse_score
    assert _parse_score("just words no json") is None
    assert _parse_score("") is None
    assert _parse_score('{"foo": "bar"}') is None  # no score field


def test_bucket_boundaries():
    from api.routers.lead_scoring import _bucket
    assert _bucket(95) == "high"
    assert _bucket(80) == "high"
    assert _bucket(79) == "medium"
    assert _bucket(50) == "medium"
    assert _bucket(49) == "low"
    assert _bucket(20) == "low"
    assert _bucket(19) == "spam"
    assert _bucket(0)  == "spam"
    assert _bucket(None) is None


# ── ICP CRUD ────────────────────────────────────────────────────────────────
def test_icp_default_is_empty():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ls = _fresh(db)
        result = ls.read_icp(ctx=_ctx("biz-a"))
        assert result["icp_description"] == ""


def test_icp_write_then_read_roundtrips():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ls = _fresh(db)
        from api.routers.lead_scoring import IcpUpdate
        ls.write_icp(IcpUpdate(icp_description="B2B SaaS, 50-200 staff, India"),
                     ctx=_ctx("biz-a"))
        result = ls.read_icp(ctx=_ctx("biz-a"))
        assert result["icp_description"] == "B2B SaaS, 50-200 staff, India"
        assert result["icp_updated_at"] is not None


def test_icp_write_rejects_non_admin():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ls = _fresh(db)
        from api.routers.lead_scoring import IcpUpdate
        with pytest.raises(HTTPException) as exc:
            ls.write_icp(IcpUpdate(icp_description="hi"),
                         ctx=_ctx("biz-a", role="member"))
        assert exc.value.status_code == 403


def test_icp_is_per_tenant():
    """Setting biz-a's ICP must NOT affect biz-b's ICP."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, ls = _fresh(db)
        from api.routers.lead_scoring import IcpUpdate
        ls.write_icp(IcpUpdate(icp_description="biz-a's ICP"), ctx=_ctx("biz-a"))
        ls.write_icp(IcpUpdate(icp_description="biz-b's ICP"), ctx=_ctx("biz-b"))

        a = ls.read_icp(ctx=_ctx("biz-a"))
        b = ls.read_icp(ctx=_ctx("biz-b"))
        assert a["icp_description"] == "biz-a's ICP"
        assert b["icp_description"] == "biz-b's ICP"


# ── Scoring ─────────────────────────────────────────────────────────────────
def test_score_without_icp_returns_actionable_reason():
    """Score-fit on a workspace with no ICP set must NOT invent a number —
    it should return null + a reason that points the user to Settings."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ls = _fresh(db)
        c = crm.create_contact("biz-a", "u", {"first_name": "Test"})

        result = ls.score_contact(business_id="biz-a", contact_id=c["id"])
        assert result["score"] is None
        assert result["icp_set"] is False
        assert "Set an Ideal Customer Profile" in result["reason"]


def test_score_persists_to_contact():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ls = _fresh(db)
        from api.routers.lead_scoring import IcpUpdate
        ls.write_icp(IcpUpdate(icp_description="B2B SaaS, 50-200 staff"),
                     ctx=_ctx("biz-a"))
        c = crm.create_contact("biz-a", "u", {
            "first_name": "Priya", "title": "Head of Sales",
            "email": "priya@b2b-saas-co.com",
        })

        with patch("api.routers.lead_scoring.llm_invoke",
                   return_value='{"score": 85, "reason": "Title and email pattern match the ICP"}'):
            result = ls.score_contact(business_id="biz-a", contact_id=c["id"])

        assert result["score"] == 85
        assert result["bucket"] == "high"

        # Verify persistence
        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT lead_score, lead_score_reason, lead_scored_at FROM nexus_contacts WHERE id = ?",
                (c["id"],),
            ).fetchone()
            assert row[0] == 85
            assert "Title" in row[1]
            assert row[2]  # scored_at populated
        finally:
            conn.close()


def test_score_handles_unparseable_llm_output():
    """When the model rambles instead of returning JSON, return null with
    an actionable message — never invent a score."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ls = _fresh(db)
        from api.routers.lead_scoring import IcpUpdate
        ls.write_icp(IcpUpdate(icp_description="x"), ctx=_ctx("biz-a"))
        c = crm.create_contact("biz-a", "u", {"first_name": "Test"})

        with patch("api.routers.lead_scoring.llm_invoke",
                   return_value="I think this looks like a 7 out of 10 fit."):
            result = ls.score_contact(business_id="biz-a", contact_id=c["id"])

        assert result["score"] is None
        assert result["icp_set"] is True
        assert "Rescore" in result["reason"]


def test_score_runs_with_sensitive_true():
    """The scoring prompt sees customer data, so the LLM call MUST set
    sensitive=True (forces local Ollama, never leaves the machine)."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ls = _fresh(db)
        from api.routers.lead_scoring import IcpUpdate
        ls.write_icp(IcpUpdate(icp_description="x"), ctx=_ctx("biz-a"))
        c = crm.create_contact("biz-a", "u", {"first_name": "Priya", "email": "priya@x.com"})

        with patch("api.routers.lead_scoring.llm_invoke",
                   return_value='{"score": 50, "reason": "x"}') as mocked:
            ls.score_contact(business_id="biz-a", contact_id=c["id"])

        assert mocked.call_args.kwargs.get("sensitive") is True, (
            "Lead-scoring prompts include customer data — sensitive=True is mandatory"
        )


def test_score_fit_404s_on_cross_tenant():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, ls = _fresh(db)
        biz_b_contact = crm.create_contact("biz-b", "u", {"first_name": "BobB"})

        with pytest.raises(HTTPException) as exc:
            ls.score_contact(business_id="biz-a", contact_id=biz_b_contact["id"])
        assert exc.value.status_code == 404
