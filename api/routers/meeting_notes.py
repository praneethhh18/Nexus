"""
Meeting notes → action items.

Paste a meeting transcript (or rough notes) → AI extracts structured action
items the user can preview, edit, and bulk-create as Tasks. Universal: works
for sales calls, internal standups, client check-ins, vendor reviews — any
kind of business that has meetings.

The endpoint only RETURNS the items. Creation goes through the existing
`POST /api/tasks` per item, so the user can edit/uncheck before committing.
That keeps the privacy model simple and avoids surprise side effects.

Privacy: transcripts often carry PII (names, account numbers, internal
strategy), so the LLM call runs sensitive=True — forced local Ollama.

Output contract:
  {
    "items": [
      {
        "title": "<imperative one-liner>",
        "description": "<optional context>",
        "priority": "low" | "normal" | "high",
        "due_hint": "<human phrase like 'this week', 'by Friday', or null>",
        "owner_hint": "<name mentioned in the notes, or null>"
      },
      ...
    ],
    "summary": "<one-sentence meeting recap>",
    "raw_count": <number of items the model emitted, before clamp>
  }
"""
from __future__ import annotations

import json
import re
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import get_current_context
from config.llm_provider import invoke as llm_invoke

router = APIRouter(tags=["meeting-notes"])


_SYSTEM = """You read meeting notes or a transcript and extract concrete \
action items. Every item must be something a person can DO — not a topic, \
not a status update. Be conservative: if no real action items are present, \
return an empty list rather than inventing tasks.

Output ONLY a JSON object on a single line, this exact shape:

  {"items": [
     {"title": "<imperative one-liner, max 160 chars>",
      "description": "<one-sentence context, or empty string>",
      "priority": "low" | "normal" | "high",
      "due_hint": "<phrase like 'this week', 'by Friday', 'next sprint', or null>",
      "owner_hint": "<first name mentioned as owner, or null>"},
     ...
   ],
   "summary": "<one-sentence recap of the meeting>"}

Priority guidance:
  - "high"   → blockers, customer-impacting, or things flagged urgent
  - "normal" → default
  - "low"    → nice-to-haves, FYI follow-ups

Output only the JSON. No code fences. No prose before or after.
"""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
_VALID_PRIORITIES = {"low", "normal", "high"}
_MAX_ITEMS = 20  # Past 20 the user is probably better off processing in chunks


class ExtractIn(BaseModel):
    notes: str = Field(..., min_length=20, max_length=40000)


def _clean_str(v, limit: int) -> str:
    if v is None:
        return ""
    return str(v).strip()[:limit]


def _coerce_item(raw) -> Optional[dict]:
    if not isinstance(raw, dict):
        return None
    title = _clean_str(raw.get("title"), 160)
    if not title:
        return None
    pri = _clean_str(raw.get("priority"), 16).lower()
    if pri not in _VALID_PRIORITIES:
        pri = "normal"
    due = raw.get("due_hint")
    due = _clean_str(due, 60) if due not in (None, "", "null") else None
    own = raw.get("owner_hint")
    own = _clean_str(own, 60) if own not in (None, "", "null") else None
    return {
        "title": title,
        "description": _clean_str(raw.get("description"), 500),
        "priority": pri,
        "due_hint": due or None,
        "owner_hint": own or None,
    }


def _parse(raw: str) -> dict:
    """Return {"items": [...], "summary": "...", "raw_count": N}.
    Honest empty state if the model produced unparseable output."""
    if not raw:
        return {"items": [], "summary": "", "raw_count": 0}
    m = _JSON_RE.search(raw)
    if not m:
        return {"items": [], "summary": "", "raw_count": 0}
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return {"items": [], "summary": "", "raw_count": 0}
    if not isinstance(obj, dict):
        return {"items": [], "summary": "", "raw_count": 0}

    raw_items = obj.get("items") if isinstance(obj.get("items"), list) else []
    cleaned: List[dict] = []
    for it in raw_items:
        c = _coerce_item(it)
        if c is not None:
            cleaned.append(c)
        if len(cleaned) >= _MAX_ITEMS:
            break

    return {
        "items": cleaned,
        "summary": _clean_str(obj.get("summary"), 400),
        "raw_count": len(raw_items),
    }


@router.post("/api/tasks/extract-from-notes")
def extract_action_items(
    payload: ExtractIn,
    ctx: dict = Depends(get_current_context),
):
    """Run extraction on the provided meeting notes. Preview-only — does not
    create tasks. The frontend lets the user edit/uncheck items, then calls
    POST /api/tasks per accepted item to commit them."""
    # ctx is required so the call is tenant-scoped and audit-attributed.
    _ = ctx["business_id"]

    prompt = f"Meeting notes:\n---\n{payload.notes}\n---"
    try:
        raw = llm_invoke(
            prompt, system=_SYSTEM,
            max_tokens=900, temperature=0.1, sensitive=True,
        )
    except Exception as e:
        logger.warning(f"[meeting-notes] LLM failed: {e}")
        raise HTTPException(503, "Couldn't reach the local model. Is Ollama running?")

    parsed = _parse(raw)
    if not parsed["items"]:
        # Honest empty state — the prompt explicitly tells the model to return
        # an empty list when there are no real action items, so this is a valid
        # outcome (not a failure) for e.g. casual chat transcripts.
        logger.info(f"[meeting-notes] no items extracted (raw_count={parsed['raw_count']})")
    return parsed
