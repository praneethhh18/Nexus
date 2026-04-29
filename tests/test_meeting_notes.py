"""
Meeting-notes → action items extraction — contract tests.

LLM is mocked. Coverage:
  - parser handles documented JSON shape
  - parser drops items with no title (titles are mandatory)
  - parser clamps invalid priority to "normal"
  - parser caps the list at _MAX_ITEMS
  - garbage LLM output → empty items list (no fabrication)
  - end-to-end call returns extracted items + summary
  - sensitive=True is enforced (transcripts often carry PII)
  - input shorter than 20 chars → 422
"""
from __future__ import annotations

import importlib
import json
import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi import HTTPException
from pydantic import ValidationError


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api.routers import meeting_notes as _mn
    importlib.reload(_mn)
    return _mn


def _ctx(business_id="biz-a", role="admin"):
    return {"user": {"id": "u-test", "name": "T"}, "business_id": business_id,
            "business_role": role}


# ── Parser ──────────────────────────────────────────────────────────────────
def test_parser_handles_clean_json():
    from api.routers.meeting_notes import _parse
    raw = json.dumps({
        "items": [
            {"title": "Send Q1 pricing to Acme",
             "description": "Reference the volume discount",
             "priority": "high", "due_hint": "this week", "owner_hint": "Alice"},
            {"title": "Schedule follow-up call",
             "description": "", "priority": "normal",
             "due_hint": None, "owner_hint": None},
        ],
        "summary": "Pricing discussion + follow-up scheduled",
    })
    out = _parse(raw)
    assert len(out["items"]) == 2
    assert out["items"][0]["title"] == "Send Q1 pricing to Acme"
    assert out["items"][0]["priority"] == "high"
    assert out["items"][0]["owner_hint"] == "Alice"
    assert out["summary"].startswith("Pricing discussion")


def test_parser_drops_items_without_title():
    from api.routers.meeting_notes import _parse
    raw = json.dumps({
        "items": [
            {"title": "", "priority": "normal"},
            {"title": "Real action", "priority": "normal"},
            {"description": "no title here", "priority": "high"},
        ],
        "summary": "",
    })
    out = _parse(raw)
    assert len(out["items"]) == 1
    assert out["items"][0]["title"] == "Real action"


def test_parser_clamps_invalid_priority():
    from api.routers.meeting_notes import _parse
    raw = json.dumps({
        "items": [{"title": "Do thing", "priority": "URGENT-NOW"}],
        "summary": "",
    })
    out = _parse(raw)
    assert out["items"][0]["priority"] == "normal"


def test_parser_caps_at_max_items():
    from api.routers.meeting_notes import _parse, _MAX_ITEMS
    raw = json.dumps({
        "items": [{"title": f"Item {i}"} for i in range(_MAX_ITEMS + 5)],
        "summary": "",
    })
    out = _parse(raw)
    assert len(out["items"]) == _MAX_ITEMS
    # raw_count reflects the model's pre-clamp count so the UI can warn.
    assert out["raw_count"] == _MAX_ITEMS + 5


def test_parser_returns_empty_on_garbage():
    from api.routers.meeting_notes import _parse
    assert _parse("the model rambled and emitted no JSON")["items"] == []
    assert _parse("")["items"] == []
    assert _parse("{not json")["items"] == []


def test_parser_normalises_null_string_hints():
    """Some models emit literal 'null' strings instead of JSON null."""
    from api.routers.meeting_notes import _parse
    raw = json.dumps({
        "items": [{"title": "X", "due_hint": "null", "owner_hint": "null"}],
        "summary": "",
    })
    out = _parse(raw)
    assert out["items"][0]["due_hint"] is None
    assert out["items"][0]["owner_hint"] is None


# ── End-to-end ──────────────────────────────────────────────────────────────
def test_extract_returns_items_and_summary():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        mn = _fresh(db)

        canned = json.dumps({
            "items": [
                {"title": "Send proposal to Globex",
                 "description": "Include 3-tier pricing",
                 "priority": "high", "due_hint": "Friday", "owner_hint": "Sam"},
                {"title": "Update CRM with new contacts",
                 "description": "", "priority": "normal",
                 "due_hint": None, "owner_hint": None},
            ],
            "summary": "Discussed Globex deal + CRM hygiene",
        })

        from api.routers.meeting_notes import ExtractIn
        with patch("api.routers.meeting_notes.llm_invoke", return_value=canned) as mocked:
            result = mn.extract_action_items(
                payload=ExtractIn(notes="Long enough notes about the meeting that we held today."),
                ctx=_ctx(),
            )

        # Privacy invariant — transcripts often contain PII.
        assert mocked.call_args.kwargs.get("sensitive") is True
        assert len(result["items"]) == 2
        assert result["items"][0]["title"] == "Send proposal to Globex"
        assert result["summary"].startswith("Discussed Globex")


def test_extract_empty_on_garbage_llm():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        mn = _fresh(db)

        from api.routers.meeting_notes import ExtractIn
        with patch("api.routers.meeting_notes.llm_invoke", return_value="meh, no real action items"):
            result = mn.extract_action_items(
                payload=ExtractIn(notes="Some meeting transcript long enough to validate."),
                ctx=_ctx(),
            )

        assert result["items"] == []
        assert result["raw_count"] == 0


def test_extract_503_when_llm_fails():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        mn = _fresh(db)

        from api.routers.meeting_notes import ExtractIn
        with patch("api.routers.meeting_notes.llm_invoke", side_effect=RuntimeError("ollama down")):
            with pytest.raises(HTTPException) as exc:
                mn.extract_action_items(
                    payload=ExtractIn(notes="Long enough notes for the validator."),
                    ctx=_ctx(),
                )
        assert exc.value.status_code == 503


def test_input_shorter_than_min_rejected():
    """Pydantic should reject < 20 chars before we hit the LLM."""
    from api.routers.meeting_notes import ExtractIn
    with pytest.raises(ValidationError):
        ExtractIn(notes="too short")
