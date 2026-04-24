"""
Admin endpoints — metrics dashboard + deep health probe (11.1 / 11.2).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api import usage_metrics
from api.auth import get_current_context
from api.reliability import deep_health

router = APIRouter(tags=["admin"])


@router.get("/api/admin/metrics")
def admin_metrics_global(days: int = 30,
                         ctx: dict = Depends(get_current_context)):
    """Global metrics across every tenant — owner/admin only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can view admin metrics")
    return usage_metrics.dashboard(business_id=None, days=max(1, min(days, 180)))


@router.get("/api/admin/metrics/tenant")
def admin_metrics_tenant(days: int = 30,
                         ctx: dict = Depends(get_current_context)):
    """Metrics scoped to the current business — any logged-in user."""
    return usage_metrics.dashboard(
        business_id=ctx["business_id"],
        days=max(1, min(days, 180)),
    )


@router.post("/api/admin/metrics/record")
def admin_metrics_record(body: dict, ctx: dict = Depends(get_current_context)):
    """Record an ad-hoc event. Lets the frontend log high-signal UI events."""
    event = (body.get("event") or "").strip()
    if not event:
        raise HTTPException(400, "event is required")
    usage_metrics.record(
        ctx["business_id"], event,
        user_id=ctx["user"]["id"],
        count=int(body.get("count") or 1),
    )
    return {"ok": True}


@router.get("/api/health/deep")
def health_deep():
    """Comprehensive health snapshot for monitoring. No auth required."""
    return deep_health()
