"""
Briefing endpoints — morning forward-looking briefing and evening
backward-looking digest. Both share the same `nexus_briefings` storage
discriminated by a `kind` column.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["briefing"])


# ── Morning briefing (forward-looking) ──────────────────────────────────────
@router.get("/api/briefing/latest")
def briefing_latest(ctx: dict = Depends(get_current_context)):
    """Return today's morning briefing for this business, or empty if none yet."""
    from agents.briefing import latest
    return latest(ctx["business_id"], kind="morning") or {}


@router.post("/api/briefing/run")
def briefing_run_now(ctx: dict = Depends(get_current_context)):
    """Generate a morning briefing right now (owner/admin only)."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can trigger a briefing")
    from agents.briefing import run_for_business
    return run_for_business(ctx["business_id"])


# ── Evening digest (backward-looking) ───────────────────────────────────────
@router.get("/api/briefing/evening/latest")
def briefing_evening_latest(ctx: dict = Depends(get_current_context)):
    """Return today's evening digest for this business, or empty if none yet."""
    from agents.briefing import latest
    return latest(ctx["business_id"], kind="evening") or {}


@router.post("/api/briefing/evening/run")
def briefing_evening_run_now(ctx: dict = Depends(get_current_context)):
    """Generate the evening digest right now (owner/admin only)."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can trigger a digest")
    from agents.briefing import run_evening_for_business
    return run_evening_for_business(ctx["business_id"])
