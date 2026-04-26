"""
Onboarding wizard endpoints — 6-step first-run flow tracked server-side so
it resumes across logins / devices.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["onboarding"])


@router.get("/api/onboarding")
def onboarding_state(ctx: dict = Depends(get_current_context)):
    """Current onboarding progress for the logged-in user in the active business."""
    from api import onboarding
    return onboarding.get_state(ctx["business_id"], ctx["user"]["id"])


@router.post("/api/onboarding/complete/{step_key}")
def onboarding_complete(step_key: str, ctx: dict = Depends(get_current_context)):
    """Mark an onboarding step as done."""
    from api import onboarding
    try:
        return onboarding.complete_step(ctx["business_id"], ctx["user"]["id"], step_key)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/api/onboarding/skip")
def onboarding_skip(ctx: dict = Depends(get_current_context)):
    """Dismiss the whole wizard. Checklist widget hides until /reopen is called."""
    from api import onboarding
    return onboarding.skip_all(ctx["business_id"], ctx["user"]["id"])


@router.post("/api/onboarding/reopen")
def onboarding_reopen(ctx: dict = Depends(get_current_context)):
    """Bring the wizard back — useful if the user accidentally clicked Skip."""
    from api import onboarding
    return onboarding.reopen(ctx["business_id"], ctx["user"]["id"])
