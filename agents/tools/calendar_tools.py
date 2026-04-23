"""Calendar tools — read upcoming Google Calendar events for the current user."""
from __future__ import annotations

from agents.tool_registry import register_tool
from api import calendar as _cal


def _upcoming_events(ctx, args):
    return _cal.list_upcoming_events(
        ctx["user_id"],
        days_ahead=int(args.get("days", 14)),
        max_results=int(args.get("limit", 20)),
    )


register_tool(
    name="upcoming_calendar_events",
    description=(
        "Get upcoming events from the current user's connected Google Calendar. "
        "Only works if the user has connected their calendar in Settings."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "days": {"type": "integer", "default": 14},
            "limit": {"type": "integer", "default": 20},
        },
    },
    handler=_upcoming_events,
)


def _calendar_status(ctx, args):
    import os
    conn = _cal.get_connection(ctx["user_id"])
    return {
        "configured": bool(os.getenv("GOOGLE_CLIENT_ID") and os.getenv("GOOGLE_CLIENT_SECRET")),
        "connected": bool(conn),
        "account_email": (conn or {}).get("account_email", ""),
    }


register_tool(
    name="calendar_status",
    description="Check whether Google Calendar is connected for the current user.",
    input_schema={"type": "object", "properties": {}},
    handler=_calendar_status,
)
