"""
Self-hosted setup wizard endpoints (9.3).

Runs before any user exists. Most endpoints are intentionally unauthenticated;
`POST /reset` is the one exception — it reopens the wizard on a live install
and requires owner/admin.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api import setup_wizard
from api.auth import get_current_context

router = APIRouter(prefix="/api/setup", tags=["setup"])


@router.get("/status")
def setup_status():
    """Snapshot of install readiness. Unauthenticated — no users may exist yet."""
    return setup_wizard.status()


@router.post("/pull-model")
def setup_pull_model(body: dict):
    """Trigger `ollama pull` for the chosen model. May take minutes on a cold pull."""
    try:
        return setup_wizard.pull_model(body.get("name") or "")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/choose-model")
def setup_choose_model(body: dict):
    try:
        return setup_wizard.choose_model(body.get("name") or "")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/complete")
def setup_complete():
    """Mark setup done. Idempotent."""
    return setup_wizard.complete()


@router.post("/reset")
def setup_reset(ctx: dict = Depends(get_current_context)):
    """Reopen the wizard — admin/owner only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can reset setup")
    return setup_wizard.reset()
