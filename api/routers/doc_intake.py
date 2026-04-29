"""
Document intake — drop a PDF or paste text → structured fields.

Universal across verticals: vendor invoices, contracts, purchase orders,
receipts, bank statements, NDAs. The model auto-detects the doc type and
returns whichever fields make sense for that type.

Two ways to feed in content:
  1. Multipart upload (`file=...`) — PDF gets text-extracted via pypdf
     before going to the LLM.
  2. Pasted text (`{"text": "..."}` JSON body) — for users on email or
     other surfaces who already have the text.

The endpoint is preview-only. It does NOT persist anything — the user
reviews the structured output and copies fields where they need them
(or, in a future iteration, presses "Create invoice" / "Create task"
to spin up a derived record).

Privacy: docs frequently carry financial / contractual PII, so the LLM
call runs sensitive=True (forced local Ollama, never cloud).

Output contract:
  {
    "doc_type": "invoice" | "contract" | "purchase_order" | "receipt"
              | "statement" | "nda" | "other",
    "summary": "<one sentence>",
    "parties": ["<entity name>", ...],          # 0..6 entries
    "dates":   [{"label": "<e.g. issue_date>", "value": "<ISO or human>"}, ...],
    "amounts": [{"label": "<e.g. total>", "value": "<as written>", "currency": "<ISO or empty>"}, ...],
    "line_items": [{"description": "...", "quantity": "...", "amount": "..."}, ...],
    "key_terms": ["<short phrase>", ...],
    "source_chars": <int>,        # length of text that went to the LLM
    "truncated": <bool>           # true if text was clipped before extraction
  }
"""
from __future__ import annotations

import io
import json
import re
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import get_current_context
from config.llm_provider import invoke as llm_invoke

router = APIRouter(tags=["doc-intake"])


# Hard caps on what we feed to the LLM. PDFs can be enormous; we'd rather
# truncate honestly than time out or blow the context window.
_MAX_CHARS_TO_LLM = 30_000
_MAX_UPLOAD_BYTES = 25 * 1024 * 1024  # 25 MB
_MIN_TEXT_LEN = 30


_SYSTEM = """You read a business document and extract structured fields. \
Common types: invoice, contract, purchase_order, receipt, statement, nda. \
Be conservative — only emit a field when the document actually contains it. \
Empty arrays are fine. Do NOT invent values.

Output ONLY a JSON object on a single line, this exact shape:

  {"doc_type": "invoice" | "contract" | "purchase_order" | "receipt" | "statement" | "nda" | "other",
   "summary": "<one sentence>",
   "parties":   ["<entity name>", ...],
   "dates":     [{"label": "<e.g. issue_date|due_date|effective_date>", "value": "<as written>"}, ...],
   "amounts":   [{"label": "<e.g. total|subtotal|tax|deposit>", "value": "<as written>", "currency": "<USD|EUR|...|empty>"}, ...],
   "line_items":[{"description": "<short>", "quantity": "<as written>", "amount": "<as written>"}, ...],
   "key_terms": ["<short phrase>", ...]}

Notes:
  - "parties" are the legal entities involved (vendor + customer for an invoice;
    parties for a contract). Skip individual signatories unless they're the only ID.
  - Keep amount values as written ($1,234.56) — don't reformat or convert currencies.
  - "key_terms" are the things a finance/legal person would skim for: payment
    terms (net 30), commitment length, auto-renewal, exclusivity, etc.
  - For unrecognised documents, set doc_type="other" and fill what you can.

Output only the JSON. No code fences. No prose before or after.
"""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
_VALID_TYPES = {"invoice", "contract", "purchase_order", "receipt",
                "statement", "nda", "other"}


class ExtractTextIn(BaseModel):
    text: str = Field(..., min_length=_MIN_TEXT_LEN, max_length=200_000)


# ── Helpers ─────────────────────────────────────────────────────────────────
def _clean_str(v, limit: int) -> str:
    if v is None:
        return ""
    return str(v).strip()[:limit]


def _coerce_kv_list(raw, key_for_label: str = "label",
                    value_keys=("value",), extra_keys=()) -> List[dict]:
    """Coerce a list-of-dicts emitted by the LLM into a clean list. Skips
    items that are missing the value field, since label-only entries are
    useless to the UI."""
    out: List[dict] = []
    if not isinstance(raw, list):
        return out
    for it in raw:
        if not isinstance(it, dict):
            continue
        record = {key_for_label: _clean_str(it.get(key_for_label), 80)}
        # Use the first non-empty value field present
        val = ""
        for vk in value_keys:
            v = _clean_str(it.get(vk), 240)
            if v:
                val = v
                break
        if not val:
            continue
        record[value_keys[0]] = val
        for ek in extra_keys:
            record[ek] = _clean_str(it.get(ek), 32)
        out.append(record)
        if len(out) >= 24:
            break
    return out


def _coerce_line_items(raw) -> List[dict]:
    out: List[dict] = []
    if not isinstance(raw, list):
        return out
    for it in raw:
        if not isinstance(it, dict):
            continue
        desc = _clean_str(it.get("description"), 240)
        if not desc:
            continue
        out.append({
            "description": desc,
            "quantity": _clean_str(it.get("quantity"), 32),
            "amount":   _clean_str(it.get("amount"), 64),
        })
        if len(out) >= 50:
            break
    return out


def _coerce_str_list(raw, limit: int = 16, item_limit: int = 200) -> List[str]:
    out: List[str] = []
    if not isinstance(raw, list):
        return out
    for v in raw:
        s = _clean_str(v, item_limit)
        if s:
            out.append(s)
        if len(out) >= limit:
            break
    return out


def _empty_extraction(source_chars: int = 0, truncated: bool = False) -> dict:
    return {
        "doc_type": "other",
        "summary": "",
        "parties": [],
        "dates": [],
        "amounts": [],
        "line_items": [],
        "key_terms": [],
        "source_chars": source_chars,
        "truncated": truncated,
    }


def _parse(raw: str, source_chars: int, truncated: bool) -> dict:
    """Parse LLM output into the canonical shape. Honest empty state on
    unparseable output — better than a fabricated invoice."""
    if not raw:
        return _empty_extraction(source_chars, truncated)
    m = _JSON_RE.search(raw)
    if not m:
        return _empty_extraction(source_chars, truncated)
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return _empty_extraction(source_chars, truncated)
    if not isinstance(obj, dict):
        return _empty_extraction(source_chars, truncated)

    dt = _clean_str(obj.get("doc_type"), 32).lower()
    if dt not in _VALID_TYPES:
        dt = "other"

    return {
        "doc_type": dt,
        "summary": _clean_str(obj.get("summary"), 400),
        "parties": _coerce_str_list(obj.get("parties"), limit=6, item_limit=120),
        "dates":   _coerce_kv_list(obj.get("dates")),
        "amounts": _coerce_kv_list(obj.get("amounts"), extra_keys=("currency",)),
        "line_items": _coerce_line_items(obj.get("line_items")),
        "key_terms": _coerce_str_list(obj.get("key_terms"), limit=12, item_limit=160),
        "source_chars": source_chars,
        "truncated": truncated,
    }


def _pdf_to_text(buf: bytes) -> str:
    """Best-effort PDF text extraction via pypdf. Returns empty string if
    the PDF is image-only (no embedded text) — caller should surface a
    helpful "looks like a scan, paste text instead" message in that case."""
    try:
        from pypdf import PdfReader
    except Exception as e:
        logger.warning(f"[doc-intake] pypdf import failed: {e}")
        raise HTTPException(500, "Server missing PDF support — paste the text instead.")
    try:
        reader = PdfReader(io.BytesIO(buf))
    except Exception as e:
        logger.info(f"[doc-intake] couldn't open PDF: {e}")
        raise HTTPException(400, "Couldn't open that file as a PDF.")
    chunks: List[str] = []
    for page in reader.pages:
        try:
            t = page.extract_text() or ""
        except Exception:
            t = ""
        if t.strip():
            chunks.append(t.strip())
    return "\n\n".join(chunks)


def _prepare_text(raw_text: str) -> tuple[str, int, bool]:
    """Clip overly-long inputs so we don't blow the context window.
    Returns (text_for_llm, char_count_before_truncation, truncated)."""
    text = (raw_text or "").strip()
    original_len = len(text)
    truncated = False
    if original_len > _MAX_CHARS_TO_LLM:
        text = text[:_MAX_CHARS_TO_LLM]
        truncated = True
    return text, original_len, truncated


def _extract_via_llm(text: str) -> dict:
    """Run the LLM call, return the parsed extraction. Raises 503 on LLM
    transport failure, otherwise always returns a (possibly empty) dict."""
    text_for_llm, source_chars, truncated = _prepare_text(text)
    if len(text_for_llm) < _MIN_TEXT_LEN:
        raise HTTPException(400, f"Text too short — need at least {_MIN_TEXT_LEN} characters.")

    prompt = f"Document content:\n---\n{text_for_llm}\n---"
    try:
        raw = llm_invoke(
            prompt, system=_SYSTEM,
            max_tokens=1200, temperature=0.1, sensitive=True,
        )
    except Exception as e:
        logger.warning(f"[doc-intake] LLM failed: {e}")
        raise HTTPException(503, "Couldn't reach the local model. Is Ollama running?")

    return _parse(raw, source_chars=source_chars, truncated=truncated)


# ── Endpoints ───────────────────────────────────────────────────────────────
@router.post("/api/documents/extract-text")
def extract_from_text(
    payload: ExtractTextIn,
    ctx: dict = Depends(get_current_context),
):
    """Extract structured fields from pasted document text."""
    _ = ctx["business_id"]  # tenant-scoped + audit-attributed
    return _extract_via_llm(payload.text)


@router.post("/api/documents/extract-upload")
async def extract_from_upload(
    file: UploadFile = File(...),
    ctx: dict = Depends(get_current_context),
):
    """Extract structured fields from an uploaded file (PDF or plain text).
    PDFs go through pypdf for text extraction first; image-only PDFs (scans)
    return a helpful 400 telling the user to paste the text instead."""
    _ = ctx["business_id"]

    # Read with a hard cap so a 500 MB upload can't OOM us.
    buf = bytearray()
    while True:
        chunk = await file.read(1024 * 64)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > _MAX_UPLOAD_BYTES:
            raise HTTPException(413, f"File too large (max {_MAX_UPLOAD_BYTES // (1024 * 1024)} MB).")

    if not buf:
        raise HTTPException(400, "Empty file.")

    name = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()
    looks_pdf = name.endswith(".pdf") or "pdf" in content_type

    if looks_pdf:
        text = _pdf_to_text(bytes(buf))
        if not text.strip():
            raise HTTPException(
                400,
                "PDF has no embedded text — looks like a scan or image-only PDF. "
                "Paste the text into the box below instead.",
            )
    else:
        # Treat as plain text. We don't try to be clever about Word docs etc.
        try:
            text = bytes(buf).decode("utf-8", errors="ignore")
        except Exception:
            raise HTTPException(400, "Couldn't read that file as text or PDF.")

    return _extract_via_llm(text)
