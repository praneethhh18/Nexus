"""
Background agent endpoints — list scheduled jobs and trigger on-demand
runs of the built-in autonomous agents (stale-deal watcher, invoice
reminder, meeting prep). The morning briefing and evening digest have
their own router.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import get_current_context
from agents.background import scheduler as _agent_sched

router = APIRouter(tags=["background_agents"])


@router.get("/api/agents/background")
def list_background_agents(ctx: dict = Depends(get_current_context)):
    return {"jobs": _agent_sched.list_jobs()}


@router.post("/api/agents/background/stale-deals/run")
def run_stale_deals_now(ctx: dict = Depends(get_current_context)):
    from agents.background.stale_deal_watcher import run_for_business
    return run_for_business(ctx["business_id"])


@router.post("/api/agents/background/invoice-reminders/run")
def run_invoice_reminders_now(ctx: dict = Depends(get_current_context)):
    from agents.background.invoice_reminder import run_for_business
    return run_for_business(ctx["business_id"])


@router.post("/api/agents/background/meeting-prep/run")
def run_meeting_prep_now(ctx: dict = Depends(get_current_context)):
    from agents.background.meeting_prep import run_for_user
    return run_for_user(ctx["user"]["id"], ctx["business_id"])
