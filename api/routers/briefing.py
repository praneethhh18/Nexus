"""
Morning briefing endpoints — fetch today's auto-generated briefing or
trigger a fresh run on demand.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["briefing"])


@router.get("/api/briefing/latest")
def briefing_latest(ctx: dict = Depends(get_current_context)):
    """Return today's briefing for this business, or empty if none yet."""
    from agents.briefing import latest
    return latest(ctx["business_id"]) or {}


@router.post("/api/briefing/run")
def briefing_run_now(ctx: dict = Depends(get_current_context)):
    """Generate a briefing right now (owner/admin only)."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can trigger a briefing")
    from agents.briefing import run_for_business
    return run_for_business(ctx["business_id"])
