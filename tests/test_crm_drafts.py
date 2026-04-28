"""
AI-drafted outreach — contract tests.

The LLM call itself is mocked because we don't want CI to depend on a
running Ollama. The tests cover:
  - parser produces three variants from the documented format
  - missing tones get filled with the fallback (so the UI is never empty)
  - cross-tenant access fails with HTTPException(404)
  - the prompt actually includes the contact's name + interactions so we
    don't ship a regression where personalisation silently disappears
"""
from __future__ import annotations

import importlib
import os
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
    from api.routers import crm_drafts as _drafts
    importlib.reload(_drafts)
    return _crm, _drafts


# ── Parser ──────────────────────────────────────────────────────────────────
def test_parser_recognises_three_well_formed_variants():
    from api.routers.crm_drafts import _parse_variants
    raw = """
VARIANT: warm
SUBJECT: Coffee next week?
BODY:
Hi Priya — saw you launched in Bangalore.
Worth a chat? — You

VARIANT: professional
SUBJECT: 15-min intro
BODY:
Priya, we run small-team CRM + invoicing in one place.
Worth a quick call? — You

VARIANT: direct
SUBJECT: 15-min Tuesday or Thursday?
BODY:
Quick one — does Tue or Thu at 3pm work? — You
""".strip()
    variants = _parse_variants(raw)
    assert len(variants) == 3
    assert {v["tone"] for v in variants} == {"warm", "professional", "direct"}
    for v in variants:
        assert v["subject"], f"Missing subject in {v}"
        assert v["body"], f"Missing body in {v}"
        assert "VARIANT" not in v["body"]


def test_parser_handles_inline_body_format():
    """Some local models put 'BODY: <text>' on one line instead of separating."""
    from api.routers.crm_drafts import _parse_variants
    raw = """
VARIANT: direct
SUBJECT: 15-min call
BODY: Quick one — does Tuesday work?
""".strip()
    variants = _parse_variants(raw)
    assert len(variants) == 1
    assert variants[0]["body"] == "Quick one — does Tuesday work?"


def test_parser_returns_empty_on_garbage():
    from api.routers.crm_drafts import _parse_variants
    assert _parse_variants("") == []
    assert _parse_variants("just some text the model rambled out") == []


# ── End-to-end (LLM mocked) ─────────────────────────────────────────────────
def test_draft_outreach_returns_three_variants_with_real_data():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, drafts = _fresh(db)

        company = crm.create_company("biz-a", "u", {"name": "Acme", "industry": "SaaS"})
        contact = crm.create_contact("biz-a", "u", {
            "first_name": "Priya", "last_name": "Sharma",
            "email": "priya@acme.com", "title": "Head of Sales",
            "company_id": company["id"],
        })
        crm.create_interaction("biz-a", "u", {
            "type": "call", "subject": "Discovery call",
            "summary": "Talked about pricing. They want a pilot.",
            "contact_id": contact["id"],
        })

        canned_llm_output = """
VARIANT: warm
SUBJECT: Pilot follow-up
BODY:
Hi Priya — great chat last week. Sending the pilot scope. — You

VARIANT: professional
SUBJECT: Pilot scope attached
BODY:
Priya, sharing the pilot scope per our call. Let me know if anything is unclear. — You

VARIANT: direct
SUBJECT: Pilot — sign off this week?
BODY:
Priya, can we sign the pilot this week? Two-week kickoff after. — You
""".strip()

        with patch("api.routers.crm_drafts.llm_invoke", return_value=canned_llm_output) as mocked:
            result = drafts.draft_outreach(business_id="biz-a", contact_id=contact["id"])

        assert mocked.called
        # The prompt must reference real signals — otherwise we shipped
        # a regression where personalisation broke silently.
        prompt = mocked.call_args.args[0]
        assert "Priya" in prompt
        assert "Acme" in prompt
        assert "Discovery call" in prompt or "pricing" in prompt
        # And it must run sensitive=True (privacy invariant).
        assert mocked.call_args.kwargs.get("sensitive") is True

        assert len(result["variants"]) == 3
        assert {v["tone"] for v in result["variants"]} == {"warm", "professional", "direct"}


def test_draft_outreach_falls_back_when_llm_returns_garbage():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, drafts = _fresh(db)
        contact = crm.create_contact("biz-a", "u", {"first_name": "Test"})

        with patch("api.routers.crm_drafts.llm_invoke", return_value="meh"):
            result = drafts.draft_outreach(business_id="biz-a", contact_id=contact["id"])
        # Three tones must be returned, even if the LLM gave us nothing.
        assert {v["tone"] for v in result["variants"]} == {"warm", "professional", "direct"}
        for v in result["variants"]:
            assert v["subject"] and v["body"]


def test_draft_outreach_404s_on_unknown_contact():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, drafts = _fresh(db)
        with pytest.raises(HTTPException) as exc:
            drafts.draft_outreach(business_id="biz-a", contact_id="contact-doesnt-exist")
        assert exc.value.status_code == 404


def test_draft_outreach_404s_on_cross_tenant_contact():
    """Multi-tenant safety: biz-a must not see biz-b's contacts even via this path."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, drafts = _fresh(db)
        biz_b_contact = crm.create_contact("biz-b", "u", {"first_name": "BobB"})
        with pytest.raises(HTTPException) as exc:
            drafts.draft_outreach(business_id="biz-a", contact_id=biz_b_contact["id"])
        assert exc.value.status_code == 404


def test_draft_outreach_handles_no_prior_interactions():
    """Cold first-touch — must still produce three variants and not pretend
    there's a relationship that doesn't exist."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, drafts = _fresh(db)
        contact = crm.create_contact("biz-a", "u", {
            "first_name": "Stranger", "email": "cold@example.com",
        })

        canned = """
VARIANT: warm
SUBJECT: Quick hello
BODY:
Saw your work and wanted to reach out. — You

VARIANT: professional
SUBJECT: 15-min intro
BODY:
Reaching out cold. Worth a 15-min chat? — You

VARIANT: direct
SUBJECT: 15-min Tue?
BODY:
Tuesday at 3pm work for a quick call? — You
""".strip()

        with patch("api.routers.crm_drafts.llm_invoke", return_value=canned) as mocked:
            result = drafts.draft_outreach(business_id="biz-a", contact_id=contact["id"])

        prompt = mocked.call_args.args[0]
        assert "NO PRIOR INTERACTIONS" in prompt, (
            "First-touch outreach must explicitly tell the model not to "
            "fabricate a prior relationship"
        )
        assert len(result["variants"]) == 3
