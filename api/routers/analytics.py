"""
Analytics endpoints — pipeline velocity, revenue forecast, agent impact,
churn risk. All read-only aggregates over the tenant's CRM + invoice data.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from api.auth import get_current_context
from api import analytics as _analytics

router = APIRouter(tags=["analytics"])


@router.get("/api/analytics/pipeline-velocity")
def analytics_pipeline_velocity(ctx: dict = Depends(get_current_context)):
    return _analytics.pipeline_velocity(ctx["business_id"])


@router.get("/api/analytics/revenue-forecast")
def analytics_revenue_forecast(horizon_months: int = 6,
                               ctx: dict = Depends(get_current_context)):
    horizon_months = max(1, min(12, horizon_months))
    return _analytics.revenue_forecast(ctx["business_id"],
                                       horizon_months=horizon_months)


@router.get("/api/analytics/agent-impact")
def analytics_agent_impact(days: int = 30,
                           ctx: dict = Depends(get_current_context)):
    days = max(1, min(180, days))
    return _analytics.agent_impact(ctx["business_id"], days=days)


@router.get("/api/analytics/churn-risk")
def analytics_churn_risk(max_deals: int = 15,
                         ctx: dict = Depends(get_current_context)):
    max_deals = max(1, min(50, max_deals))
    return _analytics.churn_risk(ctx["business_id"], max_deals=max_deals)
