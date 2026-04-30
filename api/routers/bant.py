"""
BANT extraction — read a prospect's reply, pull out structured signals.

BANT = Budget · Authority · Need · Timing. Classic qualification framework.
The model reads a pasted reply (or an interaction text) and outputs a
structured dict that the UI surfaces as a one-glance qualification card,
with a suggested stage advance when the signals are strong enough.

Stored as a JSON blob on `nexus_contacts.bant_signals` (column added at
runtime in api.crm._get_conn — same additive pattern as the source / lead_score
columns).

Privacy: prompts see customer reply content, so the LLM call runs
`sensitive=True` (forced local Ollama, never cloud).

Output contract:
  {
    "budget":     {"signal": "yes" | "no" | "unknown", "evidence": "..."},
    "authority":  {"signal": "yes" | "no" | "unknown", "evidence": "..."},
    "need":       {"signal": "yes" | "no" | "unknown", "evidence": "..."},
    "timing":     {"signal": "yes" | "no" | "unknown", "evidence": "..."},
    "confidence": 0..100,
    "suggested_stage": "lead" | "qualified" | "proposal" | "negotiation" | "won" | "lost" | null,
    "summary": "one sentence"
  }
"""
from __future__ import annotations

import json
import re
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import datetime, timezone
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api import crm as _crm
from api.auth import get_current_context
from config.llm_provider import invoke as llm_invoke
from config.db import get_conn

router = APIRouter(tags=["bant"])

CONTACTS_TABLE = "nexus_contacts"


_SYSTEM = """You qualify a sales prospect using the BANT framework: \
Budget · Authority · Need · Timing. Read the reply below and output structured \
signals. Be conservative — when the reply doesn't clearly indicate a signal, \
mark it "unknown" rather than guessing.

Output ONLY a JSON object on a single line, this exact shape:

  {"budget":     {"signal": "yes" | "no" | "unknown", "evidence": "<short quote or 'none'>"},
   "authority":  {"signal": "yes" | "no" | "unknown", "evidence": "<short quote or 'none'>"},
   "need":       {"signal": "yes" | "no" | "unknown", "evidence": "<short quote or 'none'>"},
   "timing":     {"signal": "yes" | "no" | "unknown", "evidence": "<short quote or 'none'>"},
   "confidence": <int 0..100>,
   "suggested_stage": <one of: lead, qualified, proposal, negotiation, won, lost, or null>,
   "summary":    "<one sentence>"}

Stage suggestion guide:
  - 3+ "yes" signals + medium confidence  → "qualified"
  - "Send pricing" / "discuss terms"      → "proposal"
  - "Discount" / "redlines"                → "negotiation"
  - "Approved" / "PO incoming"             → "won"
  - "Not a fit" / "decided to pass"        → "lost"
  - Otherwise (mostly unknowns)            → null (don't suggest)

Output only the JSON. No code fences. No prose before or after.
"""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
_VALID_SIGNALS = {"yes", "no", "unknown"}
_VALID_STAGES = {"lead", "qualified", "proposal", "negotiation", "won", "lost"}


class BantExtractIn(BaseModel):
    reply_text: str = Field(..., min_length=10, max_length=20000)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _normalise_signal(raw) -> Dict[str, str]:
    """Coerce an LLM-emitted signal block to the canonical shape."""
    if isinstance(raw, dict):
        sig = (raw.get("signal") or "").strip().lower()
        ev = str(raw.get("evidence") or "").strip()
    elif isinstance(raw, str):
        sig, ev = raw.strip().lower(), ""
    else:
        sig, ev = "unknown", ""
    if sig not in _VALID_SIGNALS:
        sig = "unknown"
    return {"signal": sig, "evidence": ev[:240]}


def _parse_bant(raw: str) -> Optional[Dict]:
    if not raw:
        return None
    m = _JSON_RE.search(raw)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None

    out = {
        "budget":    _normalise_signal(obj.get("budget")),
        "authority": _normalise_signal(obj.get("authority")),
        "need":      _normalise_signal(obj.get("need")),
        "timing":    _normalise_signal(obj.get("timing")),
    }
    try:
        conf = int(obj.get("confidence") or 0)
    except Exception:
        conf = 0
    out["confidence"] = max(0, min(100, conf))

    stage = obj.get("suggested_stage")
    if isinstance(stage, str) and stage.strip().lower() in _VALID_STAGES:
        out["suggested_stage"] = stage.strip().lower()
    else:
        out["suggested_stage"] = None

    out["summary"] = str(obj.get("summary") or "").strip()[:500]
    return out


def _persist(business_id: str, contact_id: str, bant: Dict) -> None:
    """Write the BANT blob to nexus_contacts.bant_signals + bant_extracted_at."""
    conn = get_conn()
    try:
        # Defensive — ensure the columns exist (api.crm._get_conn normally does this).
        cols = {r[1] for r in conn.execute(f"PRAGMA table_info({CONTACTS_TABLE})").fetchall()}
        if "bant_signals" not in cols:
            conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN bant_signals TEXT DEFAULT ''")
        if "bant_extracted_at" not in cols:
            conn.execute(f"ALTER TABLE {CONTACTS_TABLE} ADD COLUMN bant_extracted_at TEXT")

        conn.execute(
            f"UPDATE {CONTACTS_TABLE} SET bant_signals = ?, bant_extracted_at = ? "
            f"WHERE id = ? AND business_id = ?",
            (json.dumps(bant), _now(), contact_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()


@router.post("/api/crm/contacts/{contact_id}/extract-bant")
def extract_bant_api(
    contact_id: str,
    payload: BantExtractIn,
    ctx: dict = Depends(get_current_context),
):
    """Run BANT extraction on the provided reply text. Persists the result
    and returns it. Does NOT auto-advance the deal stage — that's a separate
    explicit action the user takes from the UI."""
    contact = _crm.get_contact(ctx["business_id"], contact_id)  # 404 if cross-tenant

    full_name = " ".join(filter(None, [contact.get("first_name"), contact.get("last_name")])).strip() or "(unnamed)"
    title_suffix = f" · {contact['title']}" if contact.get("title") else ""
    prompt = (
        f"Prospect: {full_name}{title_suffix}\n"
        f"Reply text:\n---\n{payload.reply_text}\n---"
    )

    try:
        raw = llm_invoke(prompt, system=_SYSTEM, max_tokens=400,
                         temperature=0.1, sensitive=True)
    except Exception as e:
        logger.warning(f"[BANT] LLM call failed for contact {contact_id}: {e}")
        raise HTTPException(503, "Couldn't reach the local model. Is Ollama running?")

    parsed = _parse_bant(raw)
    if not parsed:
        logger.warning(f"[BANT] could not parse output: {raw[:200]!r}")
        # Honest empty state — better than a fabricated qualification.
        parsed = {
            "budget":    {"signal": "unknown", "evidence": ""},
            "authority": {"signal": "unknown", "evidence": ""},
            "need":      {"signal": "unknown", "evidence": ""},
            "timing":    {"signal": "unknown", "evidence": ""},
            "confidence": 0,
            "suggested_stage": None,
            "summary": "Couldn't extract clear signals — try a longer reply or rerun.",
        }

    _persist(ctx["business_id"], contact_id, parsed)

    # Also log this as a CRM interaction so the stitch view captures it.
    try:
        _crm.create_interaction(ctx["business_id"], ctx["user"]["id"], {
            "type": "note",
            "subject": "BANT signals extracted from reply",
            "summary": parsed.get("summary", ""),
            "contact_id": contact_id,
        })
    except Exception as e:
        logger.debug(f"[BANT] interaction log failed: {e}")

    return parsed
