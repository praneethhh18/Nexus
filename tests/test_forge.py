"""
Forge AI-prospecting brainstorm — contract tests.

LLM is mocked. Coverage:
  - parser handles documented JSON shape
  - parser normalises invalid size_band → 'unknown' (never silently drops)
  - confidence clamped 0..100
  - garbage LLM output → empty list, never fabricated candidates
  - sensitive=True is enforced (privacy invariant)
  - accept flow creates company + contact tagged source='ai_outbound'
  - accept dedups by company name (skips already-existing)
  - cross-tenant safety: a candidate accepted while authenticated as biz-a
    creates the contact under biz-a, not biz-b
"""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile
from unittest.mock import patch

import pytest


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    from api.routers import lead_scoring as _ls
    importlib.reload(_ls)
    from api.routers import forge as _forge
    importlib.reload(_forge)
    return _crm, _forge, _ls


def _ctx(business_id, role="admin"):
    return {"user": {"id": "u-test", "name": "T"}, "business_id": business_id,
            "business_role": role}


# ── Parser ──────────────────────────────────────────────────────────────────
def test_parser_handles_clean_json():
    from api.routers.forge import _parse_candidates
    raw = '{"candidates": [' \
          '{"company_name": "Adworks", "industry": "Adtech", "size_band": "50-200", ' \
          ' "why_it_fits": "matches the brief", "suggested_contact_role": "Head of Sales", ' \
          ' "verify_hint": "Adworks Bangalore", "confidence": 75}' \
          ']}'
    out = _parse_candidates(raw)
    assert len(out) == 1
    assert out[0]["company_name"] == "Adworks"
    assert out[0]["confidence"] == 75


def test_parser_normalises_invalid_size_band():
    from api.routers.forge import _parse_candidates
    raw = '{"candidates": [{"company_name": "X", "size_band": "huge", "confidence": 50}]}'
    out = _parse_candidates(raw)
    assert out[0]["size_band"] == "unknown"


def test_parser_clamps_confidence():
    from api.routers.forge import _parse_candidates
    raw = '{"candidates": [{"company_name": "X", "confidence": 999}, ' \
          '{"company_name": "Y", "confidence": -10}]}'
    out = _parse_candidates(raw)
    by_name = {c["company_name"]: c for c in out}
    assert by_name["X"]["confidence"] == 100
    assert by_name["Y"]["confidence"] == 0


def test_parser_skips_candidates_without_name():
    from api.routers.forge import _parse_candidates
    raw = '{"candidates": [{"company_name": "Real"}, {"industry": "no-name"}]}'
    out = _parse_candidates(raw)
    assert len(out) == 1
    assert out[0]["company_name"] == "Real"


def test_parser_returns_empty_on_garbage():
    from api.routers.forge import _parse_candidates
    assert _parse_candidates("the model rambled") == []
    assert _parse_candidates("") == []
    assert _parse_candidates('{"not_candidates": []}') == []


# ── Brainstorm endpoint ─────────────────────────────────────────────────────
def test_brainstorm_runs_with_sensitive_true():
    """Privacy invariant — the prompt sees workspace ICP (tenant data),
    so the LLM call must set sensitive=True."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, forge, ls = _fresh(db)
        from api.routers.lead_scoring import IcpUpdate
        ls.write_icp(IcpUpdate(icp_description="B2B SaaS in India"), ctx=_ctx("biz-a"))

        from api.routers.forge import BrainstormIn
        canned = '{"candidates": [{"company_name": "ZapWidgets", "confidence": 70}]}'
        with patch("api.routers.forge.llm_invoke", return_value=canned) as mocked:
            forge.brainstorm(
                BrainstormIn(brief="D2C brands in Bangalore with 20-100 staff"),
                ctx=_ctx("biz-a"),
            )
        assert mocked.call_args.kwargs.get("sensitive") is True
        # And the prompt should include the workspace ICP we set above.
        prompt = mocked.call_args.args[0]
        assert "B2B SaaS in India" in prompt


def test_brainstorm_returns_empty_on_unparseable():
    """No fabricated candidates. If the model rambles, we return [], not made-up data."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, forge, ls = _fresh(db)

        from api.routers.forge import BrainstormIn
        with patch("api.routers.forge.llm_invoke", return_value="hmm not sure"):
            r = forge.brainstorm(BrainstormIn(brief="some realistic-length brief"),
                                 ctx=_ctx("biz-a"))
        assert r["candidates"] == []
        assert r["icp_used"] is False


# ── Accept endpoint ─────────────────────────────────────────────────────────
def test_accept_creates_company_contact_and_interaction():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, forge, _ = _fresh(db)

        from api.routers.forge import AcceptCandidate, AcceptIn
        result = forge.accept(
            AcceptIn(
                brief="D2C brands in Bangalore",
                candidates=[AcceptCandidate(
                    company_name="MeshKart",
                    industry="D2C", size_band="50-200",
                    why_it_fits="Bangalore-based, growing",
                    suggested_contact_role="Head of Growth",
                    verify_hint="MeshKart D2C Bangalore",
                    confidence=78,
                )],
            ),
            ctx=_ctx("biz-a"),
        )
        assert len(result["created"]) == 1
        assert result["skipped"] == []

        # Verify company + contact + source tag + interaction.
        created = result["created"][0]
        company = crm.get_company("biz-a", created["company_id"])
        assert company["name"] == "MeshKart"
        assert company["industry"] == "D2C"

        contact = crm.get_contact("biz-a", created["contact_id"])
        assert contact["title"] == "Head of Growth"

        conn = sqlite3.connect(db)
        try:
            row = conn.execute(
                "SELECT source FROM nexus_contacts WHERE id = ?", (created["contact_id"],),
            ).fetchone()
        finally:
            conn.close()
        assert row[0] == "ai_outbound"

        interactions = crm.list_interactions("biz-a", contact_id=created["contact_id"], limit=5)
        assert len(interactions) == 1
        assert "Forge AI prospecting" in interactions[0]["subject"]
        assert "MeshKart D2C Bangalore" in interactions[0]["summary"]


def test_accept_dedups_existing_company_name():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, forge, _ = _fresh(db)
        # Pre-create the company.
        crm.create_company("biz-a", "u", {"name": "Plotline"})

        from api.routers.forge import AcceptCandidate, AcceptIn
        result = forge.accept(
            AcceptIn(candidates=[AcceptCandidate(company_name="Plotline")]),
            ctx=_ctx("biz-a"),
        )
        assert result["created"] == []
        assert len(result["skipped"]) == 1
        assert result["skipped"][0]["reason"] == "company_exists"


def test_accept_creates_under_callers_tenant_only():
    """Cross-tenant safety: even if biz-b has a 'Plotline' company, biz-a
    accepting a 'Plotline' candidate creates a NEW one in biz-a (not
    surfacing biz-b's data and not merging across)."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, forge, _ = _fresh(db)
        # biz-b has a Plotline; biz-a does not.
        biz_b_company = crm.create_company("biz-b", "u", {"name": "Plotline"})

        from api.routers.forge import AcceptCandidate, AcceptIn
        result = forge.accept(
            AcceptIn(candidates=[AcceptCandidate(company_name="Plotline")]),
            ctx=_ctx("biz-a"),
        )
        assert len(result["created"]) == 1
        new_company_id = result["created"][0]["company_id"]
        assert new_company_id != biz_b_company["id"]

        # The new company belongs to biz-a only.
        a_companies = crm.list_companies("biz-a")
        b_companies = crm.list_companies("biz-b")
        assert any(c["id"] == new_company_id for c in a_companies)
        assert not any(c["id"] == new_company_id for c in b_companies)
