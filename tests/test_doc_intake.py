"""
Document intake — contract tests.

LLM is mocked. Coverage:
  - parser handles invoice / contract shapes
  - parser drops empty entries (label-only with no value)
  - invalid doc_type collapses to "other"
  - line items without a description are dropped (unusable for the UI)
  - garbage LLM → safe empty extraction (never fabricates)
  - oversize text is truncated, truncated=True flag set
  - sensitive=True is enforced (privacy invariant)
  - text shorter than _MIN_TEXT_LEN → 400
  - LLM transport failure → 503
"""
from __future__ import annotations

import importlib
import json
import os
import tempfile
from unittest.mock import patch

import pytest
from fastapi import HTTPException


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api.routers import doc_intake as _di
    importlib.reload(_di)
    return _di


def _ctx(business_id="biz-a", role="admin"):
    return {"user": {"id": "u-test", "name": "T"}, "business_id": business_id,
            "business_role": role}


# ── Parser ──────────────────────────────────────────────────────────────────
def test_parser_handles_invoice_shape():
    from api.routers.doc_intake import _parse
    raw = json.dumps({
        "doc_type": "invoice",
        "summary": "April invoice from Acme",
        "parties": ["Acme Corp", "Globex Inc"],
        "dates": [
            {"label": "issue_date", "value": "2025-04-15"},
            {"label": "due_date",   "value": "2025-05-15"},
        ],
        "amounts": [
            {"label": "subtotal", "value": "$5,000.00", "currency": "USD"},
            {"label": "tax",      "value": "$420.00",   "currency": "USD"},
            {"label": "total",    "value": "$5,420.00", "currency": "USD"},
        ],
        "line_items": [
            {"description": "Consulting hours", "quantity": "20", "amount": "$5,000.00"},
        ],
        "key_terms": ["net 30", "late fee 1.5%/mo"],
    })
    out = _parse(raw, source_chars=2000, truncated=False)
    assert out["doc_type"] == "invoice"
    assert "Acme Corp" in out["parties"]
    assert any(d["label"] == "issue_date" for d in out["dates"])
    assert any(a["currency"] == "USD" for a in out["amounts"])
    assert out["line_items"][0]["description"] == "Consulting hours"
    assert "net 30" in out["key_terms"]
    assert out["truncated"] is False


def test_parser_handles_contract_shape():
    from api.routers.doc_intake import _parse
    raw = json.dumps({
        "doc_type": "contract",
        "summary": "12-month MSA between Acme and Globex",
        "parties": ["Acme Corp", "Globex Inc"],
        "dates": [{"label": "effective_date", "value": "Jan 1, 2025"}],
        "amounts": [],
        "line_items": [],
        "key_terms": ["12-month commitment", "auto-renewal", "30-day termination notice"],
    })
    out = _parse(raw, source_chars=8000, truncated=False)
    assert out["doc_type"] == "contract"
    assert len(out["key_terms"]) == 3


def test_parser_drops_value_less_dates_and_amounts():
    """Label-only entries with no value are useless to the UI."""
    from api.routers.doc_intake import _parse
    raw = json.dumps({
        "doc_type": "invoice",
        "dates": [
            {"label": "issue_date", "value": "2025-04-15"},
            {"label": "due_date",   "value": ""},        # dropped
            {"label": "extra_date"},                     # dropped
        ],
        "amounts": [
            {"label": "total", "value": "$100"},
            {"label": "tax",   "value": ""},             # dropped
        ],
        "line_items": [],
        "key_terms": [],
        "parties": [],
        "summary": "",
    })
    out = _parse(raw, source_chars=100, truncated=False)
    assert len(out["dates"]) == 1
    assert len(out["amounts"]) == 1


def test_parser_drops_line_items_without_description():
    from api.routers.doc_intake import _parse
    raw = json.dumps({
        "doc_type": "invoice",
        "line_items": [
            {"description": "Real item", "quantity": "1", "amount": "$10"},
            {"description": "",          "quantity": "5", "amount": "$50"},
            {"quantity": "3", "amount": "$30"},
        ],
        "dates": [], "amounts": [], "parties": [], "key_terms": [], "summary": "",
    })
    out = _parse(raw, source_chars=100, truncated=False)
    assert len(out["line_items"]) == 1
    assert out["line_items"][0]["description"] == "Real item"


def test_parser_clamps_invalid_doc_type():
    from api.routers.doc_intake import _parse
    raw = json.dumps({"doc_type": "magic_scroll", "summary": "x",
                      "parties": [], "dates": [], "amounts": [],
                      "line_items": [], "key_terms": []})
    out = _parse(raw, source_chars=100, truncated=False)
    assert out["doc_type"] == "other"


def test_parser_returns_empty_on_garbage():
    from api.routers.doc_intake import _parse, _empty_extraction
    out = _parse("the model rambled", source_chars=500, truncated=False)
    # Should match the canonical empty shape but preserve metadata.
    assert out["doc_type"] == "other"
    assert out["parties"] == []
    assert out["amounts"] == []
    assert out["source_chars"] == 500
    assert out["truncated"] is False

    # And explicit helper sanity check:
    assert _empty_extraction(0, False)["doc_type"] == "other"


def test_truncation_clips_oversize_input():
    from api.routers.doc_intake import _prepare_text, _MAX_CHARS_TO_LLM
    big = "x" * (_MAX_CHARS_TO_LLM + 5_000)
    text, original_len, truncated = _prepare_text(big)
    assert truncated is True
    assert len(text) == _MAX_CHARS_TO_LLM
    assert original_len == _MAX_CHARS_TO_LLM + 5_000


# ── End-to-end via text endpoint ────────────────────────────────────────────
def test_extract_text_returns_structured_and_uses_sensitive():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        di = _fresh(db)

        canned = json.dumps({
            "doc_type": "purchase_order",
            "summary": "PO #1234 for office supplies",
            "parties": ["Initech Ltd"],
            "dates": [{"label": "po_date", "value": "2025-04-20"}],
            "amounts": [{"label": "total", "value": "€842.50", "currency": "EUR"}],
            "line_items": [{"description": "Standing desk", "quantity": "2", "amount": "€842.50"}],
            "key_terms": ["delivery in 5 business days"],
        })

        from api.routers.doc_intake import ExtractTextIn
        with patch("api.routers.doc_intake.llm_invoke", return_value=canned) as mocked:
            result = di.extract_from_text(
                payload=ExtractTextIn(text="Purchase Order #1234 — issued by Initech Ltd. " * 5),
                ctx=_ctx(),
            )

        # Privacy invariant: docs carry financial / contractual PII.
        assert mocked.call_args.kwargs.get("sensitive") is True
        assert result["doc_type"] == "purchase_order"
        assert result["amounts"][0]["currency"] == "EUR"
        assert result["truncated"] is False


def test_extract_text_503_when_llm_fails():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        di = _fresh(db)

        from api.routers.doc_intake import ExtractTextIn
        with patch("api.routers.doc_intake.llm_invoke", side_effect=RuntimeError("ollama down")):
            with pytest.raises(HTTPException) as exc:
                di.extract_from_text(
                    payload=ExtractTextIn(text="A long enough document body to clear the validator." * 2),
                    ctx=_ctx(),
                )
        assert exc.value.status_code == 503


def test_extract_text_safe_empty_on_garbage_llm():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        di = _fresh(db)

        from api.routers.doc_intake import ExtractTextIn
        with patch("api.routers.doc_intake.llm_invoke", return_value="i don't know"):
            result = di.extract_from_text(
                payload=ExtractTextIn(text="Random text that doesn't really look like a document but is long enough."),
                ctx=_ctx(),
            )
        assert result["doc_type"] == "other"
        assert result["parties"] == []
        assert result["line_items"] == []


def test_extract_text_input_too_short_rejected():
    """Pydantic should reject before the LLM call."""
    from api.routers.doc_intake import ExtractTextIn
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        ExtractTextIn(text="too short")
