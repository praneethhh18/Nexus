"""
AI lead scoring against the workspace's Ideal Customer Profile.

Two surfaces:

  GET  /api/workspace/icp                 — read the ICP description
  PUT  /api/workspace/icp                 — update it (admin/owner only)
  POST /api/crm/contacts/{id}/score-fit   — score (or rescore) one contact
                                            against the current ICP.

Scoring contract:
  - score is 0–100 where:
      80–100 = High fit (an obvious yes)
      50–79  = Medium  (worth a closer look)
      20–49  = Low     (probably not, send a polite no)
      0–19   = Spam    (vendor pitch, recruiter, etc.)
  - reason is a single human-readable sentence explaining the score.
  - When the workspace has no ICP set yet, scoring is a no-op that returns
    score=null and a reason saying "set an ICP first" — never silently
    invents a number.

Privacy: the scoring prompt sees contact details (name/email/title/company/
notes/source/recent interactions) so it runs `sensitive=True`. Tenant
isolation is enforced by `crm.get_contact` (already covered by the
multi-tenant test suite).
"""
from __future__ import annotations

import json
import re
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from api import crm as _crm
from api.auth import get_current_context
from config.llm_provider import invoke as llm_invoke
from config.db import get_conn

router = APIRouter(tags=["lead-scoring"])

ICP_TABLE = "nexus_workspace_settings"
CONTACTS_TABLE = "nexus_contacts"


# ── Helpers ─────────────────────────────────────────────────────────────────
def _conn():
    return get_conn()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_settings_table(conn: sqlite3.Connection) -> None:
    """The migration creates this table; this is a defensive backstop in
    case the runner hasn't run yet (e.g. in unit tests that skip it)."""
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {ICP_TABLE} (
            business_id        TEXT PRIMARY KEY,
            icp_description    TEXT DEFAULT '',
            icp_updated_at     TEXT,
            icp_updated_by     TEXT
        )
    """)


# ── ICP CRUD ────────────────────────────────────────────────────────────────
class IcpUpdate(BaseModel):
    icp_description: str = Field(..., max_length=4000)


@router.get("/api/workspace/icp")
def read_icp(ctx: dict = Depends(get_current_context)):
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        _ensure_settings_table(conn)
        row = conn.execute(
            f"SELECT icp_description, icp_updated_at, icp_updated_by FROM {ICP_TABLE} WHERE business_id = ?",
            (ctx["business_id"],),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {"icp_description": "", "icp_updated_at": None, "icp_updated_by": None}
    return dict(row)


@router.put("/api/workspace/icp")
def write_icp(payload: IcpUpdate, ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owners/admins can edit the ICP.")

    conn = _conn()
    try:
        _ensure_settings_table(conn)
        conn.execute(
            f"""INSERT INTO {ICP_TABLE} (business_id, icp_description, icp_updated_at, icp_updated_by)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(business_id) DO UPDATE SET
                    icp_description = excluded.icp_description,
                    icp_updated_at  = excluded.icp_updated_at,
                    icp_updated_by  = excluded.icp_updated_by""",
            (ctx["business_id"], payload.icp_description.strip(), _now(), ctx["user"]["id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}


def get_icp(business_id: str) -> str:
    """Module-level helper used by both this router and the public-form
    intake auto-scoring path."""
    conn = _conn()
    try:
        _ensure_settings_table(conn)
        row = conn.execute(
            f"SELECT icp_description FROM {ICP_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return ""
    return (row[0] or "").strip()


# ── Scoring ─────────────────────────────────────────────────────────────────
_SYSTEM = """You are a sales operations analyst. You score one prospective \
customer against an Ideal Customer Profile description, on a 0–100 scale, \
and write a single sentence explaining the score.

Scoring scale:
  80–100  High fit          — strong match on the key ICP signals.
  50–79   Medium fit        — partial match; worth investigating.
  20–49   Low fit            — wrong segment, but not spam.
   0–19   Spam / not a lead — recruiter, vendor pitch, abuse, irrelevant.

Output ONLY a JSON object on a single line, exactly this shape:

  {"score": <int>, "reason": "<one sentence>"}

No other text. No code fences. No prose before or after.
"""


def _build_scoring_prompt(icp: str, ctx_data: Dict) -> str:
    contact = ctx_data["contact"]
    company = ctx_data.get("company")
    interactions = ctx_data.get("interactions") or []

    full_name = " ".join(filter(None, [contact.get("first_name"), contact.get("last_name")])).strip() or "(unnamed)"
    parts = [
        f"ICP DESCRIPTION:\n{icp}",
        "",
        "PROSPECT:",
        f"  Name:    {full_name}",
        f"  Title:   {contact.get('title') or '(unknown)'}",
        f"  Email:   {contact.get('email') or '(none)'}",
        f"  Source:  {contact.get('source') or 'manual'}",
    ]
    if company:
        line = f"  Company: {company.get('name')}"
        if company.get("industry"): line += f" — {company['industry']}"
        if company.get("size"):     line += f" · {company['size']}"
        parts.append(line)
    if contact.get("notes"):
        parts.append(f"  Notes:   {(contact['notes'] or '')[:300]}")
    if interactions:
        parts.append("")
        parts.append("RECENT INTERACTIONS (newest first, max 5):")
        for it in interactions[:5]:
            kind = it.get("type", "note")
            subj = (it.get("subject") or "")[:80]
            summ = (it.get("summary") or "")[:160]
            parts.append(f"  [{kind}] {subj}" + (f" — {summ}" if summ else ""))

    parts.extend([
        "",
        "Score this prospect against the ICP. Output JSON only.",
    ])
    return "\n".join(parts)


_JSON_RE = re.compile(r"\{.*\}", re.DOTALL)


def _parse_score(raw: str) -> Optional[Dict]:
    """Extract {score, reason} from the LLM output. Returns None on
    failure — caller decides how to fall back."""
    if not raw:
        return None
    text = raw.strip()
    # If wrapped in code fences or extra prose, grab the first JSON-looking blob.
    m = _JSON_RE.search(text)
    if not m:
        return None
    try:
        obj = json.loads(m.group(0))
    except Exception:
        return None
    if not isinstance(obj, dict):
        return None
    score = obj.get("score")
    reason = obj.get("reason") or ""
    try:
        score_int = int(score)
    except Exception:
        return None
    score_int = max(0, min(100, score_int))
    return {"score": score_int, "reason": str(reason).strip()[:500]}


def _bucket(score: Optional[int]) -> Optional[str]:
    if score is None:
        return None
    if score >= 80: return "high"
    if score >= 50: return "medium"
    if score >= 20: return "low"
    return "spam"


def score_contact(business_id: str, contact_id: str) -> Dict:
    """Run a scoring pass and persist the result. Returns the new state."""
    contact = _crm.get_contact(business_id, contact_id)  # 404 if cross-tenant

    icp = get_icp(business_id)
    if not icp:
        return {
            "score": None, "bucket": None,
            "reason": "Set an Ideal Customer Profile in Settings first — scoring needs something to compare against.",
            "scored_at": None,
            "icp_set": False,
        }

    company = None
    if contact.get("company_id"):
        try: company = _crm.get_company(business_id, contact["company_id"])
        except Exception: company = None
    interactions = _crm.list_interactions(business_id, contact_id=contact_id, limit=5)

    prompt = _build_scoring_prompt(icp, {
        "contact": contact, "company": company, "interactions": interactions,
    })

    try:
        raw = llm_invoke(prompt, system=_SYSTEM, max_tokens=200,
                         temperature=0.1, sensitive=True)
    except Exception as e:
        logger.warning(f"[Scoring] LLM call failed for contact {contact_id}: {e}")
        raise HTTPException(503, "Couldn't reach the local model. Is Ollama running?")

    parsed = _parse_score(raw)
    if not parsed:
        logger.warning(f"[Scoring] could not parse output for {contact_id}: {raw[:200]!r}")
        # Don't lie with a fake number — surface the failure honestly so the
        # user can re-run. UI shows this state with a Rescore button.
        return {
            "score": None, "bucket": None,
            "reason": "The model returned a response we couldn't parse. Try Rescore.",
            "scored_at": None,
            "icp_set": True,
        }

    now = _now()
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {CONTACTS_TABLE} SET lead_score = ?, lead_score_reason = ?, lead_scored_at = ? "
            f"WHERE id = ? AND business_id = ?",
            (parsed["score"], parsed["reason"], now, contact_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "score": parsed["score"],
        "bucket": _bucket(parsed["score"]),
        "reason": parsed["reason"],
        "scored_at": now,
        "icp_set": True,
    }


@router.post("/api/crm/contacts/{contact_id}/score-fit")
def score_fit(contact_id: str, ctx: dict = Depends(get_current_context)):
    return score_contact(ctx["business_id"], contact_id)


# ── Auto-score helper for the public intake path ────────────────────────────
def auto_score_silently(business_id: str, contact_id: str) -> None:
    """Best-effort background scoring. Used by the public lead intake so
    leads land already-tagged. Never raises — the lead exists either way."""
    try:
        score_contact(business_id, contact_id)
    except Exception as e:
        logger.debug(f"[Scoring] auto-score skipped for {contact_id}: {e}")
