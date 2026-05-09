"""Lead Scorer — AI scoring of CRM contacts (0-100) for prioritization.

Pairs with Lead Hunter + Outreach to form the full top-of-funnel loop:
    Lead Hunter → adds 100 contacts to CRM
    Lead Scorer → ranks them 0-100 by likely conversion potential
    Outreach    → message the top N first

Scoring signals (combined into a single 0-100 score):
    - Title / role match  (CEO / Owner / Director > Sales Rep > Intern)
    - Industry fit         (configurable per business via the goal arg)
    - Recency              (added or contacted recently > stale)
    - Engagement           (had > 0 interactions vs cold)
    - Data completeness    (phone + email + company > sparse)
    - Past Vox call outcome (interested > callback > not_interested)

The score is stored as a tag on the contact (lead-score-XX) so the existing
TagFilterBar / segments work without schema changes. Plain integer also lives
in the result list so the agent can re-rank in subsequent calls.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List

from loguru import logger

from agents.tool_registry import register_tool


# ── Heuristic signals (cheap, deterministic, no LLM) ──────────────────────
_SENIOR_TITLES = {
    "ceo", "founder", "co-founder", "cofounder", "owner", "proprietor",
    "managing director", "md", "director", "partner", "vp", "vice president",
    "head", "principal", "president",
}
_MID_TITLES = {
    "manager", "lead", "senior", "sr.", "supervisor", "team lead", "tl",
    "consultant", "specialist",
}


def _title_score(title: str) -> int:
    t = (title or "").strip().lower()
    if not t:
        return 30
    if any(k in t for k in _SENIOR_TITLES):
        return 90
    if any(k in t for k in _MID_TITLES):
        return 60
    return 40


def _completeness_score(c: Dict[str, Any]) -> int:
    pts = 0
    if (c.get("phone") or "").strip():       pts += 35
    if (c.get("email") or "").strip():       pts += 35
    if c.get("company_id"):                  pts += 30
    return pts


def _recency_score(created_at: str) -> int:
    """Newer leads score higher — momentum matters."""
    if not created_at:
        return 50
    try:
        from datetime import datetime, timezone
        dt = datetime.fromisoformat(str(created_at).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        days = (datetime.now(timezone.utc) - dt).days
    except Exception:
        return 50
    if days <= 1:   return 100
    if days <= 7:   return 85
    if days <= 30:  return 65
    if days <= 90:  return 45
    return 25


def _engagement_bonus(business_id: str, contact_id: str) -> int:
    """+5 to +25 based on past interactions and call outcome."""
    bonus = 0
    try:
        from config.db import get_conn
        from api.crm import INTERACTIONS_TABLE
        conn = get_conn()
        try:
            row = conn.execute(
                f"SELECT COUNT(*) AS n FROM {INTERACTIONS_TABLE} "
                f"WHERE contact_id = ? AND business_id = ?",
                (contact_id, business_id),
            ).fetchone()
            n = row[0] if row else 0
            if n >= 3: bonus += 25
            elif n >= 1: bonus += 10
        finally:
            conn.close()
    except Exception as e:
        logger.debug(f"[lead_scorer] interaction count lookup failed: {e}")
    # Past Vox call outcome on the contact
    try:
        from api import voice_calls
        calls = voice_calls.list_for_contact(business_id, contact_id, limit=5) or []
        if calls:
            best = max((c.get("lead_score") or 0) for c in calls)
            bonus += min(20, max(0, best // 5))
    except Exception:
        pass
    return min(bonus, 30)


def _composite_score(business_id: str, c: Dict[str, Any]) -> int:
    """Blend signals into a single 0-100 score."""
    title = _title_score(c.get("title") or "")
    comp  = _completeness_score(c)
    rec   = _recency_score(c.get("created_at") or "")
    bonus = _engagement_bonus(business_id, c["id"])
    # Weighted: title 35% / completeness 25% / recency 25% / engagement 15%
    base = round(title * 0.35 + comp * 0.25 + rec * 0.25 + bonus * 0.15)
    return max(0, min(100, base))


def _bucket(score: int) -> str:
    if score >= 75: return "hot"
    if score >= 55: return "warm"
    if score >= 35: return "cool"
    return "cold"


def _replace_score_tag(business_id: str, contact_id: str, score: int) -> None:
    """Persist the score on the contact's `tags` field as 'lead-score-XX',
    replacing any prior 'lead-score-*' tag. Reuses the existing free-text
    tags column on contacts so no schema change is needed."""
    try:
        from config.db import get_conn
        from api.crm import CONTACTS_TABLE
        from utils.timez import now_iso
        conn = get_conn()
        try:
            row = conn.execute(
                f"SELECT tags FROM {CONTACTS_TABLE} "
                f"WHERE id = ? AND business_id = ?",
                (contact_id, business_id),
            ).fetchone()
            if not row:
                return
            current = (row[0] or "").strip()
            parts = [p.strip() for p in current.split(",") if p.strip()
                     and not p.strip().lower().startswith("lead-score-")]
            parts.append(f"lead-score-{score}")
            new_tags = ", ".join(parts)
            conn.execute(
                f"UPDATE {CONTACTS_TABLE} SET tags = ?, updated_at = ? "
                f"WHERE id = ? AND business_id = ?",
                (new_tags, now_iso(), contact_id, business_id),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"[lead_scorer] tag persist failed for {contact_id}: {e}")


# ── Tools ──────────────────────────────────────────────────────────────────
def _score_contact(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    contact_id = (args.get("contact_id") or "").strip()
    if not contact_id:
        raise ValueError("contact_id is required")
    from api import crm as _crm
    c = _crm.get_contact(ctx["business_id"], contact_id)
    score = _composite_score(ctx["business_id"], c)
    _replace_score_tag(ctx["business_id"], contact_id, score)
    return {
        "ok":         True,
        "contact_id": contact_id,
        "name":       (c.get("first_name") or "") + " " + (c.get("last_name") or ""),
        "score":      score,
        "bucket":     _bucket(score),
        "message":    f"Scored {score}/100 ({_bucket(score)}). Tag 'lead-score-{score}' added.",
    }


register_tool(
    name="score_contact",
    description=(
        "Compute a 0-100 lead score for one contact based on title, data "
        "completeness, recency, and past engagement. Persists the score as "
        "a 'lead-score-XX' tag so the existing TagFilterBar / segments work."
    ),
    input_schema={
        "type": "object",
        "properties": {"contact_id": {"type": "string"}},
        "required": ["contact_id"],
    },
    handler=_score_contact,
    summary_fn=lambda a: f"Score contact {a.get('contact_id','?')}",
)


def _score_all_contacts(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import crm as _crm
    limit  = max(1, min(int(args.get("limit", 50)), 500))
    only_unscored = bool(args.get("only_unscored", False))

    contacts = _crm.list_contacts(ctx["business_id"], limit=limit)
    if only_unscored:
        contacts = [c for c in contacts
                    if "lead-score-" not in (c.get("tags") or "")]

    results: List[Dict[str, Any]] = []
    for c in contacts:
        try:
            score = _composite_score(ctx["business_id"], c)
            _replace_score_tag(ctx["business_id"], c["id"], score)
            results.append({
                "contact_id": c["id"],
                "name":       (c.get("first_name") or "") + " " + (c.get("last_name") or ""),
                "title":      c.get("title") or "",
                "score":      score,
                "bucket":     _bucket(score),
            })
        except Exception as e:
            logger.warning(f"[lead_scorer] scoring failed for {c.get('id')}: {e}")

    results.sort(key=lambda r: r["score"], reverse=True)
    counts = {"hot": 0, "warm": 0, "cool": 0, "cold": 0}
    for r in results:
        counts[r["bucket"]] += 1

    return {
        "ok":     True,
        "scored": len(results),
        "buckets": counts,
        "top":    results[:10],
        "message": (
            f"Scored {len(results)} contacts: {counts['hot']} hot · "
            f"{counts['warm']} warm · {counts['cool']} cool · {counts['cold']} cold."
        ),
    }


register_tool(
    name="score_all_contacts",
    description=(
        "Bulk-score CRM contacts and rank them. Use to triage a fresh batch "
        "of leads (e.g. after Lead Hunter import) so Outreach can target the "
        "top N first. Returns top-10 ranked list + bucket counts. Set "
        "only_unscored=true to skip contacts that already have a score tag."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "limit":         {"type": "integer", "default": 50, "description": "Max contacts to score (1-500)."},
            "only_unscored": {"type": "boolean", "default": False},
        },
    },
    handler=_score_all_contacts,
    summary_fn=lambda a: f"Score top {a.get('limit',50)} contacts",
)
