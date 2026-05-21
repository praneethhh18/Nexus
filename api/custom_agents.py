"""
Custom agents — user-defined autonomous agents layered on top of the existing
tool registry.

A custom agent is a small contract:

    {
      name:           "Competitor Price Watcher",
      emoji:          "👀",
      description:    "Checks pricing pages daily and flags changes.",
      goal:           "Fetch the current pricing on competitor X's public page
                       and tell me if it differs from what's in memory.",
      tool_whitelist: ["search_knowledge", "create_task"],   # subset of the 51 built-ins
      interval_min:   1440,
      output_target:  "inbox"  | "briefing"  | "none",
      template_key:   "competitor_price_watcher" | null,
      enabled:        True,
    }

At runtime the agent invokes `agents.agent_loop.run_agent` with the whitelist +
a system prompt built from (name + description + goal), then routes the final
answer to the chosen output target.

Storage: `nexus_custom_agents`, one row per agent, scoped by business_id.
Scheduler: `agents.background.scheduler.rebuild_custom_jobs()` reads the table
and registers one APScheduler job per enabled agent.
"""
from __future__ import annotations

import json
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from typing import Dict, List, Optional

from fastapi import HTTPException
from loguru import logger

from config.db import get_conn
from utils.timez import now_iso

TABLE = "nexus_custom_agents"

VALID_OUTPUT_TARGETS = ("inbox", "briefing", "none")
MAX_INTERVAL_MIN = 10080   # 1 week
MIN_INTERVAL_MIN = 5


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id               TEXT PRIMARY KEY,
            business_id      TEXT NOT NULL,
            name             TEXT NOT NULL,
            emoji            TEXT DEFAULT '',
            description      TEXT DEFAULT '',
            goal             TEXT NOT NULL,
            tool_whitelist   TEXT NOT NULL DEFAULT '[]',
            interval_minutes INTEGER NOT NULL DEFAULT 1440,
            output_target    TEXT NOT NULL DEFAULT 'inbox',
            template_key     TEXT,
            enabled          INTEGER NOT NULL DEFAULT 1,
            created_at       TEXT NOT NULL,
            created_by       TEXT,
            updated_at       TEXT NOT NULL
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_biz ON {TABLE}(business_id, enabled)"
    )
    conn.commit()
    return conn


def _row_to_dict(row: sqlite3.Row) -> Dict:
    d = dict(row)
    try:
        d["tool_whitelist"] = json.loads(d["tool_whitelist"] or "[]")
    except Exception:
        d["tool_whitelist"] = []
    d["enabled"] = bool(d.get("enabled"))
    return d


# ── Validation ──────────────────────────────────────────────────────────────
def _validate_name(name: str) -> str:
    name = (name or "").strip()
    if not name:
        raise ValueError("Agent name is required")
    if len(name) > 60:
        raise ValueError("Agent name is too long (max 60 chars)")
    return name


def _validate_interval(n) -> int:
    try:
        n = int(n)
    except (TypeError, ValueError):
        raise ValueError("interval_minutes must be an integer")
    if n < MIN_INTERVAL_MIN:
        raise ValueError(f"Interval too short (min {MIN_INTERVAL_MIN} min)")
    if n > MAX_INTERVAL_MIN:
        raise ValueError(f"Interval too long (max {MAX_INTERVAL_MIN} min)")
    return n


def _validate_output(target: str) -> str:
    target = (target or "inbox").lower()
    if target not in VALID_OUTPUT_TARGETS:
        raise ValueError(f"Invalid output_target. Must be one of: {', '.join(VALID_OUTPUT_TARGETS)}")
    return target


def _validate_tools(tool_whitelist, *, strict: bool = True) -> List[str]:
    """
    Verify each requested tool actually exists in the registry.
    strict=False silently drops unknown tools — used by template cloning so
    shipping a template doesn't break every time we rename a tool.
    """
    if not tool_whitelist:
        return []
    if isinstance(tool_whitelist, str):
        tool_whitelist = [t.strip() for t in tool_whitelist.split(",") if t.strip()]
    from agents import tool_registry
    known = {t["name"] for t in tool_registry.list_tools(for_llm=False)}
    out = []
    for t in tool_whitelist:
        if t not in known:
            if strict:
                raise ValueError(f"Unknown tool: {t}")
            continue
        out.append(t)
    return out


# ── CRUD ────────────────────────────────────────────────────────────────────
def create_agent(business_id: str, user_id: str, data: Dict) -> Dict:
    name = _validate_name(data.get("name", ""))
    goal = (data.get("goal") or "").strip()
    if not goal:
        raise ValueError("Agent goal is required")
    if len(goal) > 2000:
        raise ValueError("Agent goal is too long (max 2000 chars)")
    emoji = (data.get("emoji") or "").strip()[:4]
    description = (data.get("description") or "").strip()[:500]
    tools = _validate_tools(data.get("tool_whitelist", []))
    interval = _validate_interval(data.get("interval_minutes", 1440))
    output = _validate_output(data.get("output_target"))
    template = (data.get("template_key") or "").strip()[:60] or None

    aid = f"ca-{uuid.uuid4().hex[:10]}"
    now = now_iso()
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {TABLE} "
            f"(id, business_id, name, emoji, description, goal, tool_whitelist, "
            f" interval_minutes, output_target, template_key, enabled, "
            f" created_at, created_by, updated_at) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (aid, business_id, name, emoji, description, goal,
             json.dumps(tools), interval, output, template,
             1, now, user_id, now),
        )
        conn.commit()
    finally:
        conn.close()
    return get_agent(business_id, aid)


def get_agent(business_id: str, agent_id: str) -> Dict:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE id = ? AND business_id = ?",
            (agent_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        # 404 (not 500) for both "doesn't exist" and "exists in another tenant"
        # — same response code so the API doesn't leak which tenant owns an id.
        raise HTTPException(404, f"Custom agent not found: {agent_id}")
    return _row_to_dict(row)


def list_agents(business_id: str) -> List[Dict]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? ORDER BY created_at DESC",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(r) for r in rows]


def list_all_enabled() -> List[Dict]:
    """Every enabled custom agent across every business — for the scheduler."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE enabled = 1"
        ).fetchall()
    finally:
        conn.close()
    return [_row_to_dict(r) for r in rows]


def update_agent(business_id: str, agent_id: str, updates: Dict) -> Dict:
    get_agent(business_id, agent_id)  # existence + scope check
    fields: Dict = {}
    if "name" in updates:
        fields["name"] = _validate_name(updates["name"])
    if "emoji" in updates:
        fields["emoji"] = (updates["emoji"] or "").strip()[:4]
    if "description" in updates:
        fields["description"] = (updates["description"] or "").strip()[:500]
    if "goal" in updates:
        g = (updates["goal"] or "").strip()
        if not g:
            raise ValueError("Agent goal cannot be empty")
        if len(g) > 2000:
            raise ValueError("Agent goal is too long (max 2000 chars)")
        fields["goal"] = g
    if "tool_whitelist" in updates:
        fields["tool_whitelist"] = json.dumps(_validate_tools(updates["tool_whitelist"]))
    if "interval_minutes" in updates:
        fields["interval_minutes"] = _validate_interval(updates["interval_minutes"])
    if "output_target" in updates:
        fields["output_target"] = _validate_output(updates["output_target"])
    if "enabled" in updates:
        fields["enabled"] = 1 if updates["enabled"] else 0
    if not fields:
        return get_agent(business_id, agent_id)

    fields["updated_at"] = now_iso()
    sets = ", ".join(f"{k} = ?" for k in fields.keys())
    params = list(fields.values()) + [agent_id, business_id]
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET {sets} WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
    return get_agent(business_id, agent_id)


def delete_agent(business_id: str, agent_id: str) -> None:
    conn = _conn()
    try:
        cur = conn.execute(
            f"DELETE FROM {TABLE} WHERE id = ? AND business_id = ?",
            (agent_id, business_id),
        )
        deleted = cur.rowcount
        conn.commit()
    finally:
        conn.close()
    if deleted == 0:
        # Same 404 as get/update so cross-tenant ownership stays opaque.
        raise HTTPException(404, f"Custom agent not found: {agent_id}")


# ── Runtime ─────────────────────────────────────────────────────────────────
def _build_system_prompt(agent: Dict) -> str:
    """
    Build the system prompt for the agent loop.

    Smaller open-weight models on Bedrock (Mistral Ministral 14B in
    particular) sometimes refuse to call tools and write prose like
    "I don't have access to the tools". The fix is to:
      1. List the available tools by name in the prompt itself
      2. Tell the model explicitly that it MUST call a tool first
      3. Forbid the "I don't have tools" excuse
    Bigger models (Claude, Nova Pro) tolerate the looser prompt fine.
    """
    tools = agent.get("tool_whitelist") or []
    tool_list_line = (
        ", ".join(tools) if tools else "(none — your job is purely conversational)"
    )

    base = (
        f"You are {agent['name']}, an autonomous agent for a small business.\n"
        f"Role: {agent.get('description') or '(no description provided)'}\n\n"
        f"Your goal: {agent['goal']}\n\n"
    )

    if tools:
        base += (
            f"AVAILABLE TOOLS: {tool_list_line}\n"
            "You have access to these tools right now. "
            "Do NOT say 'I don't have access to tools' or 'I would search if I could' "
            "— these tools are listed above and you can call them directly.\n\n"
            "REQUIRED BEHAVIOUR:\n"
            "1. First decide which tool(s) you need to accomplish the goal.\n"
            "2. Invoke them via the tool-use API.\n"
            "3. After tools return results, write a SHORT human-readable summary.\n\n"
            "If a tool returns empty results, report that plainly with the exact "
            "search you tried — that's a valid outcome, not a failure.\n\n"
            "FALLBACK FORMAT (only if the native tool-use API is unavailable to you): "
            "emit exactly one fenced JSON block per turn in this shape:\n"
            '```json\n'
            '{"action":"tool", "tool":"<one_of_the_tool_names_above>", "arguments":{...}}\n'
            '```\n'
            "After all needed tool calls are done, emit your final answer using:\n"
            '```json\n'
            '{"action":"final", "answer":"<your concise summary here>"}\n'
            '```\n'
            "Never write prose explaining that you can't use tools — always either "
            "use the native API or emit one of these JSON envelopes.\n"
        )
    else:
        base += (
            "You have no tools assigned. Answer purely from the goal text.\n"
        )
    return base


def _post_output(business_id: str, agent: Dict, answer: str) -> None:
    """Route the final answer to the user per agent.output_target."""
    target = agent.get("output_target", "inbox")
    if target == "none":
        return
    try:
        from api import notifications
        title = f"{agent.get('emoji', '')} {agent['name']}".strip()
        preview = (answer or "(no output)")[:400]
        if target == "inbox":
            notifications.push(
                title=title,
                message=preview,
                type="custom_agent",
                severity="info",
                business_id=business_id,
            )
        elif target == "briefing":
            # Briefing output is additive — write a notification tagged as briefing-bound.
            notifications.push(
                title=f"[Briefing] {title}",
                message=preview,
                type="briefing_section",
                severity="info",
                business_id=business_id,
            )
    except Exception as e:
        logger.warning(f"[CustomAgents] post output failed: {e}")


def run_agent_now(agent_id: str, trigger: str = "manual",
                  business_id: Optional[str] = None) -> Dict:
    """
    Run a single custom agent once. Records a `nexus_agent_runs` row so the
    history drawer surfaces it alongside the built-in agents.
    """
    from agents import run_log, agent_loop

    # Resolve the business if not given (scheduler passes None)
    if business_id is None:
        conn = _conn()
        conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                f"SELECT business_id FROM {TABLE} WHERE id = ?",
                (agent_id,),
            ).fetchone()
        finally:
            conn.close()
        if not row:
            # Same 404 as the public path so this admin entry point doesn't
            # leak which tenant owns an id either.
            raise HTTPException(404, f"Custom agent not found: {agent_id}")
        business_id = row["business_id"]

    agent = get_agent(business_id, agent_id)
    if not agent["enabled"]:
        return {"ok": False, "reason": "disabled"}

    # Capture pre-run budget snapshot so we can tell the UI whether this
    # run hit cloud or fell back to local Ollama. That distinction matters:
    # when cloud budget is exhausted, a small local model gets the request
    # and frequently refuses to use tools at all, producing junk answers
    # like "I'm a text-based AI, I can't run". The UI needs to surface
    # that as a real problem, not a vague success.
    from config import cloud_budget
    pre_cloud_ok = cloud_budget.should_allow_cloud(business_id)
    pre_usage    = cloud_budget.get_today_usage(business_id)

    run_key = f"custom:{agent_id}"
    rid = run_log.start(business_id, run_key, trigger=trigger)
    try:
        system = _build_system_prompt(agent)
        user_prompt = "Run now and tell me what you did or found."
        result = agent_loop.run_agent(
            messages=[{"role": "user", "content": user_prompt}],
            business_id=business_id,
            business_name="",      # not critical for a custom agent's focused goal
            user_id=agent.get("created_by") or "system",
            user_name=agent["name"],
            user_role="owner",
            max_steps=6,
            tool_whitelist=agent.get("tool_whitelist") or None,
            system_override=system,
            # Force the first step to call a tool. Without this, Mistral
            # Ministral 14B on Bedrock often produces "I don't have access
            # to tools" prose instead of actually calling search_knowledge
            # / list_tasks / etc. — toolChoice=any on Bedrock fixes it.
            force_first_tool=bool(agent.get("tool_whitelist")),
        )
        answer = (result or {}).get("answer", "") or ""
        tool_calls = (result or {}).get("tool_calls") or []
        post_usage = cloud_budget.get_today_usage(business_id)

        # Heuristic: if the LLM didn't call any tools AND the answer looks
        # like the classic "I'm just an AI assistant" refusal, the run is
        # effectively a no-op even if it didn't crash. Surface that as a
        # soft failure so the user knows to raise the budget / upgrade the
        # local model.
        refusal_patterns = (
            "i'm a large language model",
            "i'm a text-based ai",
            "i don't have the ability",
            "i cannot actually",
            "i am unable to physically",
            "i can't physically",
        )
        looks_refused = (
            len(tool_calls) == 0
            and any(p in (answer or "").lower() for p in refusal_patterns)
        )
        had_tools = bool(agent.get("tool_whitelist"))
        fell_back_to_local = (not pre_cloud_ok) or pre_usage.get("over_budget")

        _post_output(business_id, agent, answer)

        if looks_refused or (had_tools and len(tool_calls) == 0 and fell_back_to_local):
            run_log.finish(rid, status="skipped",
                           error="local_fallback_refused" if fell_back_to_local
                                 else "no_tools_called")
            return {
                "ok": False,
                "reason": "local_fallback_refused" if fell_back_to_local else "no_tools_called",
                "agent_id": agent_id,
                "answer": answer,
                "tool_calls": tool_calls,
                "run_id": rid,
                "budget": {
                    "tokens_used":   post_usage.get("tokens_total"),
                    "tokens_cap":    cloud_budget.get_daily_cap(business_id),
                    "over_budget":   post_usage.get("over_budget"),
                    "fell_back_to_local": fell_back_to_local,
                },
            }

        run_log.finish(rid, status="success",
                       items_produced=len(tool_calls))
        return {
            "ok":          True,
            "agent_id":    agent_id,
            "answer":      answer,
            "tool_calls":  tool_calls,
            "run_id":      rid,
            "budget": {
                "tokens_used":   post_usage.get("tokens_total"),
                "tokens_cap":    cloud_budget.get_daily_cap(business_id),
                "over_budget":   post_usage.get("over_budget"),
                "fell_back_to_local": fell_back_to_local,
            },
        }
    except Exception as e:
        logger.exception(f"[CustomAgents] run {agent_id} failed")
        run_log.finish(rid, status="error", error=str(e))
        return {"ok": False, "error": str(e), "run_id": rid}


# ── Templates ───────────────────────────────────────────────────────────────
# Curated starter agents. Users clone one → gets a new row with these defaults,
# then can edit any field before enabling.
TEMPLATES: List[Dict] = [
    {
        "key":             "competitor_price_watcher",
        "name":            "Competitor Intel Watcher",
        "emoji":           "👀",
        "description":     "Reads competitor docs and reports what's happening.",
        "goal":            "Search the knowledge base for documents categorised as 'competitor' "
                           "(use search_knowledge with category='competitor'). For each competitor "
                           "you find, write a 3-5 bullet summary covering: company focus, revenue / "
                           "size if mentioned, recent deals or partnerships, and any pricing / plans "
                           "/ discounts mentioned. If pricing is missing from the docs, say so but "
                           "still report the other intelligence. If no competitor docs are found at "
                           "all, say so plainly and ask the user to upload competitor PDFs and tag "
                           "them as 'competitor' in Documents.",
        "tool_whitelist":  ["search_knowledge"],
        "interval_minutes": 1440,
        "output_target":   "inbox",
    },
    {
        "key":             "weekly_team_digest",
        "name":            "Weekly Team Digest",
        "emoji":           "📰",
        "description":     "Summarises the past week of team activity each Monday.",
        "goal":            "Query the CRM for deals moved in the last 7 days, tasks completed, "
                           "and invoices paid. Produce a crisp 5-bullet digest for the team.",
        "tool_whitelist":  ["sql_query", "list_deals", "list_tasks", "list_invoices"],
        "interval_minutes": 10080,
        "output_target":   "inbox",
    },
    {
        "key":             "lead_scorer",
        "name":            "Lead Scorer",
        "emoji":           "🎯",
        "description":     "Rates new contacts by likely revenue potential.",
        "goal":            "List recent contacts added in the last 3 days. For each, rate "
                           "opportunity potential as high / medium / low based on title, "
                           "company size, and industry. Output a ranked list.",
        "tool_whitelist":  ["list_contacts", "get_contact"],
        "interval_minutes": 1440,
        "output_target":   "inbox",
    },
    {
        "key":             "contract_expiry_watcher",
        "name":            "Contract Expiry Watcher",
        "emoji":           "📅",
        "description":     "Flags contracts expiring in the next 30 days.",
        "goal":            "Query tasks and documents for anything whose due date or expiry is "
                           "within 30 days. Produce a short list of each with title + date.",
        "tool_whitelist":  ["list_tasks", "search_knowledge"],
        "interval_minutes": 1440,
        "output_target":   "inbox",
    },
    {
        "key":             "overdue_task_nudger",
        "name":            "Overdue Task Nudger",
        "emoji":           "⏰",
        "description":     "Notices tasks that have been overdue for more than 3 days.",
        "goal":            "List all open tasks with a due_date more than 3 days past today. "
                           "Summarise by assignee and suggest what to do next for each.",
        "tool_whitelist":  ["list_tasks"],
        "interval_minutes": 1440,
        "output_target":   "inbox",
    },
    {
        "key":             "social_mention_monitor",
        "name":            "Social Mention Monitor",
        "emoji":           "📣",
        "description":     "Scans the knowledge base for recent mentions of your brand.",
        "goal":            "Search the knowledge base for recent mentions of our business name or "
                           "products. Prefer documents categorised as 'social' or 'press' if any "
                           "exist (use search_knowledge with category='social'). Note the top 3 "
                           "most relevant mentions with a one-line summary each.",
        "tool_whitelist":  ["search_knowledge"],
        "interval_minutes": 4320,   # every 3 days
        "output_target":   "inbox",
    },
]


def list_templates() -> List[Dict]:
    return list(TEMPLATES)


def create_from_template(business_id: str, user_id: str, template_key: str,
                         overrides: Optional[Dict] = None) -> Dict:
    tpl = next((t for t in TEMPLATES if t["key"] == template_key), None)
    if not tpl:
        raise ValueError(f"Unknown template: {template_key}")
    data = dict(tpl)
    data["template_key"] = template_key
    # Templates reference aspirational tool names; silently drop any that
    # aren't in the live registry so clone never fails due to a rename.
    data["tool_whitelist"] = _validate_tools(data.get("tool_whitelist", []), strict=False)
    if overrides:
        data.update(overrides)
    return create_agent(business_id, user_id, data)
