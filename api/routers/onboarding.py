"""
Onboarding wizard endpoints — 6-step first-run flow tracked server-side so
it resumes across logins / devices.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.auth import get_current_context

router = APIRouter(tags=["onboarding"])


class ProfileExtras(BaseModel):
    business_type: str = ""
    company_size:  str = ""
    primary_goal:  str = ""


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


@router.get("/api/onboarding/industry-preset")
def onboarding_industry_preset(ctx: dict = Depends(get_current_context)):
    """Preview the preset for the active business industry."""
    from api.businesses import get_business
    from api.industry_setup import get_preset

    biz = get_business(ctx["business_id"]) or {}
    return get_preset(biz.get("industry") or "")


@router.post("/api/onboarding/industry-setup")
def onboarding_industry_setup(ctx: dict = Depends(get_current_context)):
    """Apply industry-aware workspace defaults and mark the agents step done."""
    from api import onboarding
    from api.businesses import get_business
    from api.industry_setup import apply_industry_setup

    biz = get_business(ctx["business_id"]) or {}
    result = apply_industry_setup(
        ctx["business_id"],
        ctx["user"]["id"],
        biz.get("industry") or "",
    )
    try:
        state = onboarding.complete_step(ctx["business_id"], ctx["user"]["id"], "agents")
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"setup": result, "onboarding": state}


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


@router.post("/api/onboarding/profile-extras")
def onboarding_profile_extras(req: ProfileExtras, ctx: dict = Depends(get_current_context)):
    """Persist business_type / company_size / primary_goal into the active
    business's settings.profile. Called by the wizard alongside the existing
    update_business call so these structured fields become first-class
    workspace metadata instead of free-text inside the description."""
    from api import onboarding
    profile = onboarding.set_profile_extras(
        ctx["business_id"],
        business_type=req.business_type,
        company_size=req.company_size,
        primary_goal=req.primary_goal,
    )
    return {"profile": profile}


@router.get("/api/onboarding/profile-extras")
def onboarding_get_profile_extras(ctx: dict = Depends(get_current_context)):
    """Read what's already saved — used by the wizard to pre-fill form
    fields on re-entry and by the dashboard to tune KPI selection."""
    from api import onboarding
    return {"profile": onboarding.get_profile_extras(ctx["business_id"])}
