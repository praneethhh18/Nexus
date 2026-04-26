"""
Action approval queue endpoints.

When agent mode wants to take a side-effecting action (send an email,
create an invoice, etc.), it posts to the approval queue and waits for
the user to approve or reject. This router exposes the inbox for that
queue.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from api.auth import get_current_context
from agents import approval_queue as _approvals

router = APIRouter(tags=["approvals"])


@router.get("/api/approvals")
def list_approvals(status: Optional[str] = None, limit: int = 100,
                   ctx: dict = Depends(get_current_context)):
    return {
        "actions": _approvals.list_actions(ctx["business_id"], status=status, limit=limit),
        "pending_count": _approvals.pending_count(ctx["business_id"]),
    }


@router.get("/api/approvals/pending-count")
def approvals_pending_count(ctx: dict = Depends(get_current_context)):
    return {"pending_count": _approvals.pending_count(ctx["business_id"])}


@router.get("/api/approvals/{action_id}")
def get_approval(action_id: str, ctx: dict = Depends(get_current_context)):
    return _approvals.get_action(ctx["business_id"], action_id)


@router.post("/api/approvals/{action_id}/approve")
def approve_action(action_id: str, ctx: dict = Depends(get_current_context)):
    return _approvals.approve_action(ctx["business_id"], ctx["user"]["id"], action_id)


@router.post("/api/approvals/{action_id}/reject")
def reject_action(action_id: str, body: dict = None,
                  ctx: dict = Depends(get_current_context)):
    reason = (body or {}).get("reason", "")
    return _approvals.reject_action(
        ctx["business_id"], ctx["user"]["id"], action_id, reason=reason,
    )
