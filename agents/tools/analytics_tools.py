"""Analytics tools — expose forecast and health reports to the agent."""
from __future__ import annotations

from agents.tool_registry import register_tool
from api import analytics as _a


def _pipeline_velocity(ctx, args):
    return _a.pipeline_velocity(ctx["business_id"])


register_tool(
    name="pipeline_velocity",
    description=(
        "Report average days spent in each deal stage and stage→won conversion "
        "rates. Use to answer 'how fast is our pipeline moving' questions."
    ),
    input_schema={"type": "object", "properties": {}},
    handler=_pipeline_velocity,
)


def _revenue_forecast(ctx, args):
    return _a.revenue_forecast(
        ctx["business_id"],
        horizon_months=int(args.get("horizon_months", 6)),
    )


register_tool(
    name="revenue_forecast",
    description=(
        "Weighted pipeline revenue forecast, grouped by expected-close month, "
        "for the next N months (default 6). Uses deal value × probability %."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "horizon_months": {"type": "integer", "default": 6, "minimum": 1, "maximum": 12},
        },
    },
    handler=_revenue_forecast,
)


def _agent_impact(ctx, args):
    return _a.agent_impact(ctx["business_id"], days=int(args.get("days", 30)))


register_tool(
    name="agent_impact",
    description=(
        "How much work has the agent done in the last N days (default 30): "
        "tool calls, approvals, estimated minutes saved."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "days": {"type": "integer", "default": 30, "minimum": 1, "maximum": 180},
        },
    },
    handler=_agent_impact,
)


def _churn_risk(ctx, args):
    return _a.churn_risk(ctx["business_id"], max_deals=int(args.get("max_deals", 15)))


register_tool(
    name="churn_risk",
    description=(
        "Score the top open deals by risk of stalling (silence days, time-in-"
        "stage, missed close dates). Returns deals ranked high→low with factors "
        "and, for high-risk ones, a suggested next action."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "max_deals": {"type": "integer", "default": 15, "minimum": 1, "maximum": 50},
        },
    },
    handler=_churn_risk,
)
