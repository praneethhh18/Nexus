"""Custom agent management tools — let the user spin up new agents in chat.

The CRUD + scheduler are already implemented in api.custom_agents and
agents.background.scheduler. This file just wraps them as agent tools so the
LLM can create / list / delete / run-now in response to plain-English asks
like:

    "Every Friday at 5 PM, send me a WhatsApp summary of overdue invoices."
    "Create an agent that watches for new tickets and pings me on Slack."
    "Show me all my custom agents."
    "Delete the Friday digest agent."
"""
from __future__ import annotations

import re
from typing import Any, Dict

from loguru import logger

from agents.tool_registry import register_tool


# ── Frequency → interval_minutes coercion ──────────────────────────────────
# The existing scheduler is interval-based (not cron), so phrases like
# "every Friday at 5 PM" can only be honored as "weekly" (7 days). We keep
# the conversion straightforward and predictable.
def _frequency_to_minutes(spec: str) -> int:
    """Best-effort English → interval_minutes conversion.

    Accepted forms:
        'every 30 minutes', 'every 2 hours', 'every 6 hours',
        'hourly', 'daily', 'weekly', 'monthly',
        'twice a day', '3 times a day',
        plain integer (treated as minutes).

    Returns minutes (clamped to the existing module's MIN/MAX limits).
    """
    if not spec:
        return 1440  # default: daily

    if isinstance(spec, (int, float)):
        return max(5, min(10080, int(spec)))

    s = str(spec).strip().lower()

    # plain integer → minutes
    if s.isdigit():
        return max(5, min(10080, int(s)))

    # 'every N hours/minutes/days' — check FIRST so it doesn't lose to
    # the substring 'minute' / 'hour' alias matchers below.
    m = re.match(r"every\s+(\d+)\s*(minute|min|hour|hr|day)s?", s)
    if m:
        n = int(m.group(1))
        unit = m.group(2)
        if unit.startswith("min"):
            return max(5, min(10080, n))
        if unit.startswith("hour") or unit.startswith("hr"):
            return max(5, min(10080, n * 60))
        if unit.startswith("day"):
            return max(5, min(10080, n * 1440))

    # 'N times a day' → 1440 / N
    m = re.match(r"(\d+)\s*times?\s*(a|per)\s*day", s)
    if m:
        n = int(m.group(1))
        if n > 0:
            return max(5, min(10080, 1440 // n))

    # Word-based shortcuts (kept multi-word so they don't match arbitrary
    # substrings of more specific phrases like 'every 30 minutes').
    aliases = {
        "every hour":    60,
        "hourly":        60,
        "twice a day":   720,
        "twice daily":   720,
        "daily":         1440,
        "every day":     1440,
        "every morning": 1440,
        "every evening": 1440,
        "weekly":        10080,
        "every week":    10080,
        "every monday":  10080,
        "every friday":  10080,
        "monthly":       10080,    # capped at the 1-week max
        "every month":   10080,
    }
    for k, v in aliases.items():
        if k in s:
            return v

    # Fallback: daily
    logger.debug(f"[custom_agent_tools] could not parse frequency {spec!r}, defaulting to daily")
    return 1440


def _humanize_minutes(n: int) -> str:
    if n >= 10080:
        return "weekly"
    if n >= 1440:
        d = n // 1440
        return f"every {d} day{'s' if d != 1 else ''}"
    if n >= 60:
        h = n // 60
        return f"every {h} hour{'s' if h != 1 else ''}"
    return f"every {n} minute{'s' if n != 1 else ''}"


# ── Tools ──────────────────────────────────────────────────────────────────
def _create_custom_agent(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    business_id = ctx["business_id"]
    user_id     = ctx["user_id"]

    name = (args.get("name") or "").strip()
    goal = (args.get("goal") or "").strip()
    if not name or not goal:
        raise ValueError("Both 'name' and 'goal' are required.")

    interval = _frequency_to_minutes(args.get("frequency") or args.get("interval_minutes") or 1440)
    output   = (args.get("output_target") or "inbox").lower()
    tools    = args.get("tool_whitelist") or args.get("tools") or []

    payload = {
        "name":             name,
        "goal":             goal,
        "description":      (args.get("description") or "")[:500],
        "emoji":            (args.get("emoji") or "🤖").strip()[:4],
        "tool_whitelist":   tools,
        "interval_minutes": interval,
        "output_target":    output,
    }

    from api import custom_agents
    agent = custom_agents.create_agent(business_id, user_id, payload)

    # Trigger the scheduler to pick up the new agent immediately so the user
    # doesn't need to restart the API to see their first run.
    try:
        from agents.background.scheduler import rebuild_custom_jobs
        rebuild_custom_jobs()
    except Exception as e:
        # Not fatal — APScheduler may not have started yet (e.g. in a worker
        # process). The agent will get registered on the next boot.
        logger.warning(f"[custom_agent_tools] scheduler rebuild failed: {e}")

    return {
        "ok":               True,
        "agent_id":         agent["id"],
        "name":             agent["name"],
        "interval_minutes": agent["interval_minutes"],
        "frequency":        _humanize_minutes(agent["interval_minutes"]),
        "tools":            agent["tool_whitelist"],
        "output_target":    agent["output_target"],
        "message":          (
            f"Created agent '{name}' — runs {_humanize_minutes(agent['interval_minutes'])}, "
            f"output to {agent['output_target']}. First run will trigger on the next "
            f"interval window."
        ),
    }


register_tool(
    name="create_custom_agent",
    description=(
        "Create a new user-defined agent that runs on a schedule. Use when the "
        "user asks for a recurring autonomous task — e.g. 'every Friday send "
        "me overdue invoices on WhatsApp', 'check the pricing page daily and "
        "tell me if it changes', 'every morning summarise yesterday's "
        "activity'. The new agent picks the right tools to use from the "
        "registry at run time. Frequency accepts plain English ('daily', "
        "'every 6 hours', 'weekly') or a number of minutes."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Short agent name shown in lists and notifications. e.g. 'Friday Invoice Digest'.",
            },
            "goal": {
                "type": "string",
                "description": (
                    "What the agent should do every time it runs. Be specific: "
                    "'Check overdue invoices and send a WhatsApp message with "
                    "the total amount and top 5 contacts to chase'. The agent "
                    "uses this as its sole instruction at run time."
                ),
            },
            "frequency": {
                "type": "string",
                "description": (
                    "How often to run. Accepts 'hourly', 'daily', 'weekly', "
                    "'every 30 minutes', 'every 6 hours', etc. Default: 'daily'."
                ),
                "default": "daily",
            },
            "tool_whitelist": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Optional list of tool names the agent is allowed to use. "
                    "Leave empty to give it access to all standard tools. "
                    "Examples: ['list_invoices', 'send_outbound'] for an "
                    "invoice-focused agent."
                ),
            },
            "output_target": {
                "type": "string",
                "enum":        ["inbox", "briefing", "none"],
                "description": (
                    "Where the agent's output goes. 'inbox' (default) creates "
                    "an in-app notification. 'briefing' adds it to the morning "
                    "briefing. 'none' for silent runs."
                ),
                "default":     "inbox",
            },
            "emoji": {
                "type": "string",
                "description": "Optional emoji for the agent. Default 🤖.",
                "default":     "🤖",
            },
            "description": {
                "type": "string",
                "description": "One-line summary of what this agent does (for the UI list).",
            },
        },
        "required": ["name", "goal"],
    },
    handler=_create_custom_agent,
    summary_fn=lambda a: f"New custom agent: {a.get('name','?')} ({a.get('frequency','daily')})",
)


# ── list / delete / run-now ────────────────────────────────────────────────
def _list_custom_agents(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import custom_agents
    rows = custom_agents.list_agents(ctx["business_id"])
    return {
        "ok":     True,
        "count":  len(rows),
        "agents": [
            {
                "id":                a["id"],
                "name":              a["name"],
                "emoji":             a.get("emoji", ""),
                "description":       a.get("description", ""),
                "goal":              a["goal"][:200],
                "frequency":         _humanize_minutes(a["interval_minutes"]),
                "interval_minutes":  a["interval_minutes"],
                "tools":             a.get("tool_whitelist") or [],
                "output_target":     a.get("output_target", "inbox"),
                "enabled":           a["enabled"],
            }
            for a in rows
        ],
    }


register_tool(
    name="list_custom_agents",
    description="List all user-defined (custom) agents for this business with their schedules and goals.",
    input_schema={"type": "object", "properties": {}},
    handler=_list_custom_agents,
    summary_fn=lambda a: "List custom agents",
)


def _delete_custom_agent(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = (args.get("agent_id") or "").strip()
    if not agent_id:
        raise ValueError("agent_id is required")
    from api import custom_agents
    custom_agents.delete_agent(ctx["business_id"], agent_id)
    try:
        from agents.background.scheduler import rebuild_custom_jobs
        rebuild_custom_jobs()
    except Exception as e:
        logger.warning(f"[custom_agent_tools] scheduler rebuild after delete failed: {e}")
    return {"ok": True, "agent_id": agent_id, "message": f"Deleted custom agent {agent_id}."}


register_tool(
    name="delete_custom_agent",
    description="Delete a user-defined custom agent by id. Stops it from running again.",
    input_schema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "string", "description": "Custom agent id (ca-…)"},
        },
        "required": ["agent_id"],
    },
    handler=_delete_custom_agent,
    summary_fn=lambda a: f"Delete custom agent {a.get('agent_id','?')}",
    requires_approval=True,  # destructive, mirror the *_delete pattern in the registry
)


def _run_custom_agent_now(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    agent_id = (args.get("agent_id") or "").strip()
    if not agent_id:
        raise ValueError("agent_id is required")
    from api import custom_agents
    out = custom_agents.run_agent_now(agent_id, trigger="manual",
                                       business_id=ctx["business_id"])
    return out


register_tool(
    name="run_custom_agent_now",
    description=(
        "Trigger a custom agent to run immediately (one-off), without waiting "
        "for its next scheduled interval. Returns the agent's output."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "agent_id": {"type": "string", "description": "Custom agent id (ca-…)"},
        },
        "required": ["agent_id"],
    },
    handler=_run_custom_agent_now,
    summary_fn=lambda a: f"Run custom agent {a.get('agent_id','?')} now",
)
