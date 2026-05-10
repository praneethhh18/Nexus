"""Calendar tools — read AND book Google Calendar events for the current user."""
from __future__ import annotations

import re
from datetime import datetime, timedelta

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


# ── Booking ─────────────────────────────────────────────────────────────────
def _coerce_iso(s: str, default_tz: str = "+05:30") -> str:
    """Tolerant parse of times the LLM is likely to produce.

    Accepts:
        '2026-05-12T16:00:00+05:30'   (already E-formatted)
        '2026-05-12T16:00:00'          (assume IST)
        '2026-05-12 16:00'             (assume IST)
        '2026-05-12 4:00 PM'           (assume IST)
    Returns a clean ISO-8601 string.
    """
    if not s:
        raise ValueError("time is required")
    s = s.strip()
    # Already a full ISO string with timezone
    if re.search(r"[+-]\d{2}:?\d{2}$|Z$", s):
        return s
    # Try a few common formats; fall through to ISO + IST suffix
    for fmt in (
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %I:%M %p",
        "%Y-%m-%d %I:%M%p",
    ):
        try:
            dt = datetime.strptime(s, fmt)
            # Treat naive times as IST (the SMB market default)
            return dt.strftime("%Y-%m-%dT%H:%M:%S") + default_tz
        except ValueError:
            continue
    raise ValueError(f"Could not parse time: {s!r}. Use ISO-8601 like 2026-05-12T16:00:00+05:30")


def _book_event(ctx, args):
    title = (args.get("title") or "Meeting").strip()
    start_raw = args.get("start") or ""
    duration = int(args.get("duration_minutes", 30))
    end_raw  = args.get("end") or ""

    start_iso = _coerce_iso(start_raw)
    if end_raw:
        end_iso = _coerce_iso(end_raw)
    else:
        # Compute end from duration
        # Re-parse start_iso (we just normalized it) to add duration
        try:
            start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
        except ValueError:
            raise ValueError(f"Could not re-parse normalized start {start_iso!r}")
        end_dt = start_dt + timedelta(minutes=max(5, min(duration, 480)))
        end_iso = end_dt.isoformat()

    attendees = args.get("attendees") or []
    if isinstance(attendees, str):
        attendees = [a.strip() for a in re.split(r"[,;\s]+", attendees) if "@" in a]

    out = _cal.create_event(
        ctx["user_id"],
        summary=title,
        start_iso=start_iso, end_iso=end_iso,
        description=(args.get("description") or "")[:2000],
        location=(args.get("location") or "")[:200],
        attendees=attendees,
        add_meet_link=bool(args.get("add_meet_link", False)),
    )
    return {
        "ok":           True,
        "event_id":     out.get("id"),
        "summary":      out.get("summary"),
        "start":        out.get("start"),
        "end":          out.get("end"),
        "link":         out.get("html_link"),
        "meet_link":    out.get("hangout_link"),
        "attendees":    out.get("attendees", []),
        "message":      (
            f"Booked '{out.get('summary')}' for {out.get('start')} "
            f"({len(out.get('attendees') or [])} attendee(s))."
        ),
    }


register_tool(
    name="book_calendar_event",
    description=(
        "Book a new event on the user's Google Calendar. Use when the user "
        "asks to schedule a meeting, block time, or set a reminder. Times "
        "should be ISO-8601 (e.g. '2026-05-12T16:00:00+05:30'); naive times "
        "are treated as IST. If only `start` + `duration_minutes` is given, "
        "`end` is computed. Set add_meet_link=true to attach a Google Meet "
        "link automatically."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "title":            {"type": "string", "description": "Event title."},
            "start":            {"type": "string", "description": "Start time (ISO-8601 or 'YYYY-MM-DD HH:MM')."},
            "end":              {"type": "string", "description": "End time. Optional if duration_minutes is given."},
            "duration_minutes": {"type": "integer", "default": 30, "description": "Used if end isn't provided. 5-480."},
            "description":      {"type": "string"},
            "location":         {"type": "string"},
            "attendees":        {"type": "array", "items": {"type": "string"}, "description": "List of attendee email addresses."},
            "add_meet_link":    {"type": "boolean", "default": False, "description": "Auto-attach a Google Meet link."},
        },
        "required": ["title", "start"],
    },
    handler=_book_event,
    summary_fn=lambda a: f"Book '{a.get('title','?')}' at {a.get('start','?')}",
    requires_approval=True,  # external write to a connected account — gate by approval
)
