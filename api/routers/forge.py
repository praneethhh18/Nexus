"""
Forge — AI-driven prospecting brainstorm.

The honest version. Real web-scraping prospecting (visit pages, extract
contact info, dedup against the workspace) needs external APIs or fragile
scrapers — both fight the local-first brand. What we do instead is
*brainstorming*: the LLM suggests candidate companies that match the
workspace's Ideal Customer Profile + the user's brief, each with a
verify-hint. The user reviews each candidate and marks the ones worth
adding as real contacts.

The candidates ARE NOT verified leads. The frontend shows this clearly,
and we tag accepted contacts with source='ai_outbound' so they're
visible in the CRM Leads tab as the AI-prospecting cohort.

Two endpoints:
  POST /api/crm/leads/forge-brainstorm  — generate candidates from a brief
  POST /api/crm/leads/forge-accept       — create contacts for the user-
                                            curated subset

Privacy: the brainstorm prompt sees the workspace's ICP description
(tenant data) so the LLM call runs `sensitive=True` — forced local Ollama.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api import crm as _crm
from api.auth import get_current_context
from config.llm_provider import invoke as llm_invoke

router = APIRouter(tags=["forge"])


_SYSTEM = """You are a sales-prospecting brainstormer. The user describes a target \
profile; you suggest 8-12 candidate companies that MIGHT match. You are NOT \
claiming the companies definitely exist or have those exact attributes — \
you are brainstorming a starter list the user will verify.

Output rules:
  - 8-12 candidates. Variety over quantity.
  - Each candidate: realistic-looking company name + industry + size band +
    a one-sentence "why it fits" + suggested contact role + a verify-hint
    (a Google query the user can run to confirm) + a confidence score 0-100.
  - Don't invent obviously-fake names. Use plausible patterns ("Adworks",
    "MeshKart", "Plotline AI"). If you don't have specific knowledge, say so
    via lower confidence — never claim a fact you can't back.
  - No politicians, no celebrities, no real-person names.

Output PRECISELY in this JSON shape on one line, no fences, no prose:

  {"candidates": [
     {"company_name": "...",
      "industry": "...",
      "size_band": "<10 | 10-50 | 50-200 | 200-1000 | 1000+ | unknown",
      "why_it_fits": "...",
      "suggested_contact_role": "...",
      "verify_hint": "Google search term that would confirm this exists",
      "confidence": 0..100}
  ]}
"""


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)
_VALID_SIZE_BANDS = {"<10", "10-50", "50-200", "200-1000", "1000+", "unknown"}


class BrainstormIn(BaseModel):
    brief: str = Field(..., min_length=10, max_length=2000,
                        description="Natural-language prospecting brief, e.g. 'D2C brands in Bangalore with 20-100 staff that raised in the last 18 months'")


class AcceptCandidate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: Optional[str] = Field(None, max_length=120)
    size_band: Optional[str] = Field(None, max_length=20)
    why_it_fits: Optional[str] = Field(None, max_length=400)
    suggested_contact_role: Optional[str] = Field(None, max_length=120)
    verify_hint: Optional[str] = Field(None, max_length=200)
    confidence: Optional[int] = Field(None, ge=0, le=100)


class AcceptIn(BaseModel):
    candidates: List[AcceptCandidate] = Field(..., min_length=1, max_length=50)
    brief: Optional[str] = Field(None, max_length=2000,
                                  description="Original brief — logged on each created contact for context.")


def _get_icp(business_id: str) -> str:
    """Read the workspace ICP without importing the lead_scoring module
    at top level (avoids a circular import in fresh test setups)."""
    from api.routers.lead_scoring import get_icp
    return get_icp(business_id)


def _normalise(c: Dict) -> Optional[Dict]:
    """Coerce a single LLM-emitted candidate into the canonical shape.
    Returns None if the candidate is missing the bare minimum (a name)."""
    if not isinstance(c, dict):
        return None
    name = str(c.get("company_name") or c.get("name") or "").strip()
    if not name:
        return None
    size = str(c.get("size_band") or "unknown").strip()
    if size not in _VALID_SIZE_BANDS:
        size = "unknown"
    try:
        conf = int(c.get("confidence") or 0)
    except Exception:
        conf = 0
    conf = max(0, min(100, conf))
    return {
        "company_name":          name[:200],
        "industry":              str(c.get("industry") or "")[:120],
        "size_band":             size,
        "why_it_fits":           str(c.get("why_it_fits") or "")[:400],
        "suggested_contact_role": str(c.get("suggested_contact_role") or "")[:120],
        "verify_hint":           str(c.get("verify_hint") or "")[:200],
        "confidence":            conf,
    }


def _parse_candidates(raw: str) -> List[Dict]:
    if not raw:
        return []
    m = _JSON_RE.search(raw)
    if not m:
        return []
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return []
    if not isinstance(obj, dict):
        return []
    items = obj.get("candidates") or []
    if not isinstance(items, list):
        return []
    out = []
    for c in items:
        norm = _normalise(c)
        if norm:
            out.append(norm)
    # Sort: highest-confidence first, ties broken by name.
    out.sort(key=lambda x: (-x["confidence"], x["company_name"]))
    return out[:12]


@router.post("/api/crm/leads/forge-brainstorm")
def brainstorm(payload: BrainstormIn, ctx: dict = Depends(get_current_context)):
    """
    Generate candidate companies for a prospecting brief.

    The candidates are AI suggestions, not verified leads — the response
    shape includes a verify_hint per candidate that the user can run as
    a Google query to confirm.
    """
    icp = _get_icp(ctx["business_id"])

    parts = [f"Brief: {payload.brief.strip()}"]
    if icp:
        parts.append(f"\nWorkspace ICP context (use this as additional fit criteria):\n{icp}")
    else:
        parts.append("\n(No ICP set — rely on the brief alone for fit reasoning.)")

    prompt = "\n".join(parts)

    try:
        raw = llm_invoke(
            prompt, system=_SYSTEM, max_tokens=1200, temperature=0.6,
            sensitive=True,
        )
    except Exception as e:
        logger.warning(f"[Forge] LLM call failed: {e}")
        raise HTTPException(503, "Couldn't reach the local model. Is Ollama running?")

    candidates = _parse_candidates(raw)
    return {
        "candidates": candidates,
        "icp_used": bool(icp),
        "brief": payload.brief.strip(),
    }


@router.post("/api/crm/leads/forge-accept")
def accept(payload: AcceptIn, ctx: dict = Depends(get_current_context)):
    """
    Convert user-curated candidates into real contacts, tagged
    source='ai_outbound'. Each candidate becomes one contact + one logged
    interaction so the conversation timeline shows where it came from.

    Cross-tenant safety: contacts are scoped to ctx['business_id'] by
    construction (we never accept a foreign contact_id from the client).
    """
    business_id = ctx["business_id"]
    user_id = ctx["user"]["id"]

    created: List[Dict] = []
    skipped: List[Dict] = []

    for c in payload.candidates:
        # Light dedup — if a contact with this exact company name already
        # exists in the workspace, skip rather than creating a phantom.
        try:
            existing = _crm.list_companies(business_id, search=c.company_name, limit=10)
            already = next(
                (e for e in existing if (e.get("name") or "").strip().lower() == c.company_name.strip().lower()),
                None,
            )
        except Exception:
            already = None

        if already:
            skipped.append({"company_name": c.company_name, "reason": "company_exists"})
            continue

        # Create a placeholder company + a contact attached to it.
        try:
            company = _crm.create_company(business_id, user_id, {
                "name":     c.company_name,
                "industry": c.industry or "",
                "size":     c.size_band or "",
                "notes":    (c.why_it_fits or "")[:500],
            })
        except Exception as e:
            skipped.append({"company_name": c.company_name, "reason": f"company_create_failed: {e}"})
            continue

        # Contact: we don't have a real person yet, so create a role-shaped
        # placeholder ("Head of Growth at Adworks") that the user fills in
        # after they verify.
        role = c.suggested_contact_role or "Head of Sales"
        contact = _crm.create_contact(business_id, user_id, {
            "first_name": "(unknown)",
            "last_name":  "",
            "title":      role,
            "company_id": company["id"],
        })
        # Stamp the source — create_contact doesn't accept it directly.
        try:
            from config.settings import DB_PATH
            import sqlite3
            conn = sqlite3.connect(DB_PATH)
            conn.execute(
                "UPDATE nexus_contacts SET source = ? WHERE id = ?",
                ("ai_outbound", contact["id"]),
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"[Forge] source stamp failed: {e}")

        # Log a note interaction with the AI's reasoning + verify hint —
        # gives the user the trail when they review the contact later.
        try:
            summary = (c.why_it_fits or "").strip()
            hint = (c.verify_hint or "").strip()
            if hint:
                summary = (summary + f"\n\nVerify: search Google for: {hint}").strip()
            if payload.brief:
                summary = (f"From brief: {payload.brief.strip()[:200]}\n\n" + summary).strip()
            _crm.create_interaction(business_id, user_id, {
                "type": "note",
                "subject": "Forge AI prospecting candidate",
                "summary": summary[:2000],
                "contact_id": contact["id"],
                "company_id": company["id"],
            })
        except Exception as e:
            logger.debug(f"[Forge] interaction log failed: {e}")

        created.append({
            "company_id": company["id"],
            "contact_id": contact["id"],
            "company_name": c.company_name,
        })

    return {"created": created, "skipped": skipped}
