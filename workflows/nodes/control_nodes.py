"""
Control-flow nodes for the workflow engine — the Phase 2 additions:

    for_each_node     — iterate over a list from ctx and run an inline action
                        once per item. Keeps the DAG single-dimensional by
                        collapsing the inner loop into one node.
    error_handler     — wrap an inline action in try/catch; on failure run a
                        fallback action.
    trigger_agent     — fire a built-in or custom agent from within a workflow,
                        merging its summary back into ctx.

Each node reads its inner "action spec" from config:
    {
      "action_type":   "send_email" | "create_task" | "http_request" | ...,
      "action_config": {...}          # the usual config for that node type
    }

Keeping the action nested instead of spanning multiple DAG nodes avoids the
need to rewire the executor for dynamic branching — one node, many iterations.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List

from loguru import logger


# ── Dispatch helper: run a single named node inline ─────────────────────────
def _run_inline(action_type: str, action_config: Dict[str, Any],
                ctx: Dict[str, Any]) -> Dict[str, Any]:
    """Execute one node by type + config, sharing ctx with the caller."""
    # Avoid a circular import with executor.
    from workflows.executor import _get_runner
    runner = _get_runner(action_type)
    if runner is None:
        raise ValueError(f"Unknown inline action_type: {action_type}")
    return runner(action_config, ctx)


# ── 1. for_each_node — loop over a list, run an action per item ────────────
def run_for_each_node(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Iterate a list from ctx[source_field] and run `action_type` once per item.

    config:
        source_field:  dotted path into ctx whose value is iterable (default "output")
        max_items:     hard cap so a buggy source can't DoS the scheduler
        action_type:   node type to run per item
        action_config: config for the inner node
    """
    source_field = config.get("source_field", "output")
    max_items = max(1, min(int(config.get("max_items", 50) or 50), 200))
    action_type = config.get("action_type")
    action_config = config.get("action_config") or {}

    if not action_type:
        ctx["output"] = "for_each: no action_type configured"
        return ctx

    items = _read_path(ctx, source_field)
    if items is None or not isinstance(items, (list, tuple)):
        # Try to parse JSON lists left in ctx['output']
        if isinstance(items, str):
            try:
                parsed = json.loads(items)
                if isinstance(parsed, list):
                    items = parsed
            except Exception:
                items = None
    if not isinstance(items, (list, tuple)) or not items:
        ctx["output"] = f"for_each: no iterable found at '{source_field}'"
        return ctx

    items = list(items)[:max_items]
    summaries: List[str] = []
    errors: List[str] = []

    for idx, item in enumerate(items):
        inner_ctx = dict(ctx)
        inner_ctx["_item"] = item
        inner_ctx["_item_index"] = idx
        inner_ctx["output"] = item if not isinstance(item, (dict, list)) else ""
        try:
            result = _run_inline(action_type, action_config, inner_ctx)
            summaries.append(str(result.get("output", ""))[:200])
        except Exception as e:
            logger.exception(f"[for_each] iteration {idx} failed")
            errors.append(f"#{idx}: {e}")

    ctx["output"] = (
        f"for_each ran {action_type} on {len(items)} item(s)"
        + (f"; {len(errors)} failed" if errors else "")
    )
    ctx["_for_each_results"] = summaries
    ctx["_for_each_errors"] = errors
    return ctx


# ── 2. error_handler — try an action, fall back on failure ─────────────────
def run_error_handler(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run `action_type`; if it raises, run `fallback_type`. The fallback has the
    original error appended to ctx so it can notify Discord, log, etc.

    config:
        action_type / action_config       — the guarded action
        fallback_type / fallback_config   — what to do on failure (optional)
    """
    action_type = config.get("action_type")
    action_config = config.get("action_config") or {}
    fallback_type = config.get("fallback_type")
    fallback_config = config.get("fallback_config") or {}

    if not action_type:
        ctx["output"] = "error_handler: no action_type configured"
        return ctx

    try:
        ctx = _run_inline(action_type, action_config, ctx)
        ctx["_error_handler_branch"] = "success"
        return ctx
    except Exception as e:
        logger.warning(f"[error_handler] {action_type} failed: {e} — running fallback")
        ctx["_error_message"] = str(e)
        ctx["_error_handler_branch"] = "fallback"
        if not fallback_type:
            ctx["output"] = f"Action failed ({e}) — no fallback configured"
            return ctx
        try:
            return _run_inline(fallback_type, fallback_config, ctx)
        except Exception as e2:
            logger.exception("[error_handler] fallback also failed")
            ctx["output"] = f"Both action and fallback failed: {e} / {e2}"
            ctx["_error_handler_branch"] = "fallback_failed"
            return ctx


# ── 3. trigger_agent — run a built-in or custom agent inline ───────────────
def run_trigger_agent(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fire another agent from within a workflow. Supports both built-in agents
    (by agent_key) and custom agents (by custom_agent_id).

    config:
        agent_type:       'builtin' | 'custom'
        agent_key:        one of the 6 built-in keys (if agent_type = 'builtin')
        custom_agent_id:  id in nexus_custom_agents         (if agent_type = 'custom')
    """
    agent_type = (config.get("agent_type") or "builtin").lower()
    business_id = ctx.get("_business_id") or "default"

    try:
        if agent_type == "custom":
            agent_id = config.get("custom_agent_id") or ""
            if not agent_id:
                raise ValueError("trigger_agent: custom_agent_id is required")
            from api import custom_agents
            result = custom_agents.run_agent_now(
                agent_id, trigger="workflow", business_id=business_id,
            )
            ctx["output"] = (result or {}).get("answer", "") or "(custom agent returned nothing)"
            ctx["_agent_result"] = result
            return ctx

        # Built-in agents
        key = config.get("agent_key") or ""
        from agents import run_log
        rid = run_log.start(business_id, key, trigger="workflow")
        try:
            output = _run_builtin(key, business_id, ctx)
            run_log.finish(rid, status="success",
                           items_produced=_count_items(output))
        except Exception as e:
            run_log.finish(rid, status="error", error=str(e))
            raise
        ctx["output"] = str(output)[:2000] if output else f"Ran {key}"
        ctx["_agent_result"] = output
        return ctx
    except Exception as e:
        logger.exception(f"[trigger_agent] {agent_type} failed")
        ctx["output"] = f"trigger_agent failed: {e}"
        return ctx


def _run_builtin(agent_key: str, business_id: str, ctx: Dict[str, Any]):
    """Dispatch by key to the same runners /api/agents/{key}/run uses."""
    if agent_key == "morning_briefing":
        from agents.briefing import run_for_business
        return run_for_business(business_id)
    if agent_key == "invoice_reminder":
        from agents.background.invoice_reminder import run_for_business
        return run_for_business(business_id)
    if agent_key == "stale_deal_watcher":
        from agents.background.stale_deal_watcher import run_for_business
        return run_for_business(business_id)
    if agent_key == "email_triage":
        from agents.email_triage import run_for_business
        return run_for_business(business_id)
    if agent_key == "memory_consolidate":
        from agents.summarizer import consolidate_business_memory
        return consolidate_business_memory(business_id, apply_changes=True)
    if agent_key == "meeting_prep":
        from agents.background.meeting_prep import run_for_user
        user_id = ctx.get("_user_id") or "default"
        return run_for_user(user_id, business_id)
    raise ValueError(f"Unknown built-in agent_key: {agent_key}")


def _count_items(result) -> int:
    if not isinstance(result, dict):
        return 0
    for k in ("queued", "created", "processed", "stale_deals",
              "candidates", "meetings", "consolidated", "count"):
        v = result.get(k)
        if isinstance(v, int):
            return v
    return 0


# ── Utilities ──────────────────────────────────────────────────────────────
def _read_path(ctx: Dict[str, Any], path: str):
    """Dotted-path lookup into ctx. 'foo.bar' → ctx['foo']['bar']."""
    if not path:
        return None
    cur: Any = ctx
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            return None
        if cur is None:
            return None
    return cur
