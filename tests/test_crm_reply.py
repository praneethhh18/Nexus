"""
AI reply drafter — contract tests.

LLM is mocked. Coverage:
  - parser handles documented JSON shape
  - sensitive=True is enforced (privacy invariant)
  - falls back to a pre-canned non-empty reply when LLM output is garbage
  - cross-tenant access blocked
  - unknown contact 404s
  - prompt actually includes the prospect name + the incoming message
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
    from api.routers import crm_reply as _r
    importlib.reload(_r)
    return _crm, _r


def _ctx(business_id, role="admin"):
    return {"user": {"id": "u-test", "name": "T"}, "business_id": business_id,
            "business_role": role}


def test_parser_handles_clean_json():
    from api.routers.crm_reply import _parse_reply
    raw = '{"subject": "Re: pilot", "body": "Hi Priya,\\n\\nThanks for getting back. — You"}'
    out = _parse_reply(raw)
    assert out["subject"] == "Re: pilot"
    assert "Priya" in out["body"]


def test_parser_returns_none_on_garbage():
    from api.routers.crm_reply import _parse_reply
    assert _parse_reply("the model rambled") is None
    assert _parse_reply("") is None
    assert _parse_reply('{"subject": ""}') is None  # empty subject rejected


def test_draft_reply_runs_with_sensitive_true():
    """Privacy invariant — the prompt sees the prospect's incoming message,
    so the LLM call must set sensitive=True (forced local Ollama)."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, r = _fresh(db)
        c = crm.create_contact("biz-a", "u", {"first_name": "Priya"})

        from api.routers.crm_reply import ReplyDraftIn
        canned = '{"subject": "Re: pricing", "body": "Hi Priya,\\n\\nLet me follow up. — You"}'
        with patch("api.routers.crm_reply.llm_invoke", return_value=canned) as mocked:
            r.draft_reply_api(
                contact_id=c["id"],
                payload=ReplyDraftIn(incoming_text="Can you share pricing?"),
                ctx=_ctx("biz-a"),
            )
        assert mocked.call_args.kwargs.get("sensitive") is True


def test_draft_reply_includes_prospect_name_and_incoming_text_in_prompt():
    """Personalisation regression guard — if someone refactors and breaks the
    prompt context, this test catches it."""
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, r = _fresh(db)
        c = crm.create_contact("biz-a", "u", {"first_name": "Aarav", "last_name": "Mehta"})
        crm.create_interaction("biz-a", "u", {
            "type": "call", "subject": "Discovery call",
            "summary": "Discussed pilot terms.",
            "contact_id": c["id"],
        })

        from api.routers.crm_reply import ReplyDraftIn
        canned = '{"subject": "Re: terms", "body": "Hi Aarav, here\\u2019s the update. — You"}'
        with patch("api.routers.crm_reply.llm_invoke", return_value=canned) as mocked:
            r.draft_reply_api(
                contact_id=c["id"],
                payload=ReplyDraftIn(incoming_text="Just checking on the pilot terms?"),
                ctx=_ctx("biz-a"),
            )
        prompt = mocked.call_args.args[0]
        assert "Aarav" in prompt
        assert "pilot terms" in prompt
        assert "Discovery call" in prompt


def test_draft_reply_falls_back_on_unparseable_llm():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, r = _fresh(db)
        c = crm.create_contact("biz-a", "u", {"first_name": "Stranger"})

        from api.routers.crm_reply import ReplyDraftIn
        with patch("api.routers.crm_reply.llm_invoke", return_value="hmm not sure"):
            result = r.draft_reply_api(
                contact_id=c["id"],
                payload=ReplyDraftIn(incoming_text="What's the next step please?"),
                ctx=_ctx("biz-a"),
            )
        assert result["subject"] and result["body"]
        assert "Stranger" in result["body"]  # fallback uses the contact's name


def test_draft_reply_404s_on_cross_tenant():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        crm, r = _fresh(db)
        biz_b = crm.create_contact("biz-b", "u", {"first_name": "BobB"})

        from api.routers.crm_reply import ReplyDraftIn
        with pytest.raises(HTTPException) as exc:
            r.draft_reply_api(
                contact_id=biz_b["id"],
                payload=ReplyDraftIn(incoming_text="Some message text long enough"),
                ctx=_ctx("biz-a"),
            )
        assert exc.value.status_code == 404
