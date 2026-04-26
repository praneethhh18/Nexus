"""
Agents router — the big one.

Covers six endpoint groups:
    /api/agents/activity            timeline of all agent activity
    /api/agents/personas            list + rename + enable/disable built-ins
    /api/agents/{agent_key}/run     on-demand fire of a built-in agent
    /api/agents/runs                run log query
    /api/agents/schedule            per-business interval overrides
    /api/agents/nudges              proactive suggestion queue
    /api/custom-agents/...          user-defined agents (CRUD + templates + run)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from pydantic import BaseModel

from api.auth import get_current_context

router = APIRouter(tags=["agents"])


class _PersonaPatch(BaseModel):
    name: Optional[str] = None
    enabled: Optional[bool] = None


# ── Activity + personas ────────────────────────────────────────────────────
@router.get("/api/agents/activity")
def agents_activity(hours: int = 48, limit: int = 50,
                    ctx: dict = Depends(get_current_context)):
    """Unified timeline of what every agent did in the last `hours` hours."""
    from agents.activity import recent
    hours = max(1, min(hours, 720))
    limit = max(1, min(limit, 200))
    return recent(ctx["business_id"], hours=hours, limit=limit)


@router.get("/api/agents/personas")
def agents_list_personas(ctx: dict = Depends(get_current_context)):
    """Return all 6 agent personas (name, role tag, description, last activity)."""
    from agents.personas import list_personas
    from agents import run_log

    personas = list_personas(ctx["business_id"])
    summary = run_log.summary(ctx["business_id"], hours=24)
    for p in personas:
        last = run_log.last_run(ctx["business_id"], p["agent_key"])
        p["last_run"] = last
        p["run_stats_24h"] = summary.get(p["agent_key"], {"success": 0, "error": 0, "skipped": 0})
    return personas


@router.patch("/api/agents/personas/{agent_key}")
def agents_patch_persona(agent_key: str, body: _PersonaPatch,
                         ctx: dict = Depends(get_current_context)):
    """Rename an agent + toggle enabled. Owner/admin only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can rename agents")
    from agents.personas import set_name, set_enabled, get_persona
    if body.name is not None:
        try:
            set_name(ctx["business_id"], agent_key, body.name)
        except ValueError as e:
            raise HTTPException(400, str(e))
        except KeyError:
            raise HTTPException(404, f"Unknown agent: {agent_key}")
    if body.enabled is not None:
        try:
            set_enabled(ctx["business_id"], agent_key, body.enabled)
        except KeyError:
            raise HTTPException(404, f"Unknown agent: {agent_key}")
    return get_persona(ctx["business_id"], agent_key)


# ── Run log + schedule ─────────────────────────────────────────────────────
@router.get("/api/agents/runs")
def agents_list_runs(agent_key: Optional[str] = None, limit: int = 50,
                     ctx: dict = Depends(get_current_context)):
    """Recent per-run log — what ran, when, and whether it succeeded."""
    from agents import run_log
    return {"runs": run_log.list_runs(ctx["business_id"], agent_key=agent_key, limit=limit)}


@router.get("/api/agents/schedule")
def agents_schedule_list(ctx: dict = Depends(get_current_context)):
    """Per-agent interval schedule for this business."""
    from api import agent_schedule
    return {
        "schedule": agent_schedule.list_schedule(ctx["business_id"]),
        "presets":  agent_schedule.INTERVAL_PRESETS_MIN,
    }


@router.patch("/api/agents/schedule/{agent_key}")
def agents_schedule_set(agent_key: str, body: dict,
                        ctx: dict = Depends(get_current_context)):
    """Set a per-agent interval override for this business."""
    from api import agent_schedule
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can change agent schedules")
    minutes = body.get("interval_minutes")
    try:
        return agent_schedule.set_interval(ctx["business_id"], agent_key, minutes)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/api/agents/schedule/{agent_key}")
def agents_schedule_reset(agent_key: str, ctx: dict = Depends(get_current_context)):
    """Remove the override — agent goes back to the shipped default."""
    from api import agent_schedule
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can change agent schedules")
    try:
        return agent_schedule.reset_interval(ctx["business_id"], agent_key)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Nudges ─────────────────────────────────────────────────────────────────
@router.get("/api/agents/nudges")
def agents_list_nudges(ctx: dict = Depends(get_current_context)):
    """Active proactive nudges — things the team noticed and wants permission to act on."""
    from agents.nudges import list_active
    return list_active(ctx["business_id"])


@router.post("/api/agents/nudges/{nudge_id}/dismiss")
def agents_dismiss_nudge(nudge_id: str, ctx: dict = Depends(get_current_context)):
    """Hide this nudge for the rest of today (UTC). Returns fresh nudge list."""
    from agents.nudges import dismiss, list_active
    dismiss(ctx["business_id"], nudge_id)
    return list_active(ctx["business_id"])


@router.post("/api/agents/nudges/{nudge_id}/accept")
def agents_accept_nudge(nudge_id: str, ctx: dict = Depends(get_current_context)):
    """Act on a nudge. Looks up by id, executes (run_agent or navigate), returns {result, next_nudges}."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can act on nudges")

    from agents.nudges import list_active, dismiss
    nudges = list_active(ctx["business_id"])
    nudge = next((n for n in nudges if n["id"] == nudge_id), None)
    if not nudge:
        raise HTTPException(404, "Nudge not active (already handled or dismissed)")

    action = nudge.get("action") or {}
    result: dict = {"kind": action.get("kind")}

    if action.get("kind") == "run_agent":
        agent_key = action.get("agent_key")
        if agent_key == "morning_briefing":
            from agents.briefing import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        elif agent_key == "invoice_reminder":
            from agents.background.invoice_reminder import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        elif agent_key == "stale_deal_watcher":
            from agents.background.stale_deal_watcher import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        elif agent_key == "meeting_prep":
            from agents.background.meeting_prep import run_for_user
            result["detail"] = run_for_user(ctx["user"]["id"], ctx["business_id"])
        elif agent_key == "email_triage":
            from agents.email_triage import run_for_business
            result["detail"] = run_for_business(ctx["business_id"])
        else:
            raise HTTPException(400, f"Unknown agent in nudge action: {agent_key}")
    elif action.get("kind") == "navigate":
        result["path"] = action.get("path")
    else:
        raise HTTPException(400, f"Unknown action kind: {action.get('kind')}")

    dismiss(ctx["business_id"], nudge_id)
    return {"result": result, "next_nudges": list_active(ctx["business_id"])}


# ── Run built-in agent on demand ───────────────────────────────────────────
@router.post("/api/agents/{agent_key}/run")
def agents_run_now(agent_key: str, ctx: dict = Depends(get_current_context)):
    """On-demand trigger for a specific built-in agent. Owner/admin only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can run agents on demand")

    business_id = ctx["business_id"]
    user_id = ctx["user"]["id"]

    from agents import run_log
    from agents.background.scheduler import _count_items

    def _do_run():
        if agent_key == "morning_briefing":
            from agents.briefing import run_for_business
            result = run_for_business(business_id)
            return result, {"narrative_mode": result.get("mode"),
                            "delivered": result.get("delivered_channels", [])}
        if agent_key == "invoice_reminder":
            from agents.background.invoice_reminder import run_for_business
            result = run_for_business(business_id)
            return result, result
        if agent_key == "stale_deal_watcher":
            from agents.background.stale_deal_watcher import run_for_business
            result = run_for_business(business_id)
            return result, result
        if agent_key == "meeting_prep":
            from agents.background.meeting_prep import run_for_user
            result = run_for_user(user_id, business_id)
            return result, result
        if agent_key == "email_triage":
            from agents.email_triage import run_for_business
            result = run_for_business(business_id)
            return result, result
        if agent_key == "memory_consolidate":
            from agents.summarizer import consolidate_business_memory
            result = consolidate_business_memory(business_id, apply_changes=True)
            return result, result
        raise HTTPException(404, f"Unknown agent: {agent_key}")

    run_id = run_log.start(business_id, agent_key, trigger="manual")
    try:
        result, detail = _do_run()
        run_log.finish(run_id, status="success",
                       items_produced=_count_items(result or {}))
        return {"ok": True, "agent_key": agent_key, "detail": detail, "run_id": run_id}
    except HTTPException:
        run_log.finish(run_id, status="error", error="unknown agent")
        raise
    except Exception as e:
        logger.exception(f"[AgentRun] {agent_key} failed: {e}")
        run_log.finish(run_id, status="error", error=str(e))
        raise HTTPException(500, f"{agent_key} failed: {e}")


# ── Custom agents ──────────────────────────────────────────────────────────
def _rebuild_after_crud():
    """Refresh the scheduler after a custom-agent CRUD so changes take effect without restart."""
    try:
        from agents.background.scheduler import rebuild_custom_jobs
        rebuild_custom_jobs()
    except Exception as e:
        logger.warning(f"[CustomAgents] rebuild_custom_jobs failed: {e}")


@router.get("/api/custom-agents")
def custom_agents_list(ctx: dict = Depends(get_current_context)):
    from api import custom_agents
    return custom_agents.list_agents(ctx["business_id"])


@router.post("/api/custom-agents")
def custom_agents_create(body: dict, ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can create custom agents")
    from api import custom_agents
    try:
        agent = custom_agents.create_agent(ctx["business_id"], ctx["user"]["id"], body)
    except ValueError as e:
        raise HTTPException(400, str(e))
    _rebuild_after_crud()
    return agent


@router.get("/api/custom-agents/templates")
def custom_agents_templates(ctx: dict = Depends(get_current_context)):
    from api import custom_agents
    return custom_agents.list_templates()


@router.post("/api/custom-agents/from-template")
def custom_agents_from_template(body: dict, ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can create custom agents")
    from api import custom_agents
    try:
        agent = custom_agents.create_from_template(
            ctx["business_id"], ctx["user"]["id"],
            body.get("template_key") or "",
            overrides=body.get("overrides") or {},
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    _rebuild_after_crud()
    return agent


@router.get("/api/custom-agents/{agent_id}")
def custom_agents_get(agent_id: str, ctx: dict = Depends(get_current_context)):
    from api import custom_agents
    try:
        return custom_agents.get_agent(ctx["business_id"], agent_id)
    except KeyError:
        raise HTTPException(404, "Custom agent not found")


@router.patch("/api/custom-agents/{agent_id}")
def custom_agents_update(agent_id: str, body: dict,
                         ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can edit custom agents")
    from api import custom_agents
    try:
        agent = custom_agents.update_agent(ctx["business_id"], agent_id, body)
    except KeyError:
        raise HTTPException(404, "Custom agent not found")
    except ValueError as e:
        raise HTTPException(400, str(e))
    _rebuild_after_crud()
    return agent


@router.delete("/api/custom-agents/{agent_id}")
def custom_agents_delete(agent_id: str, ctx: dict = Depends(get_current_context)):
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can delete custom agents")
    from api import custom_agents
    custom_agents.delete_agent(ctx["business_id"], agent_id)
    _rebuild_after_crud()
    return {"ok": True}


@router.post("/api/custom-agents/{agent_id}/run")
def custom_agents_run_now(agent_id: str, ctx: dict = Depends(get_current_context)):
    """On-demand fire. Owner/admin only — mirrors built-in Run Now policy."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can run agents on demand")
    from api import custom_agents
    try:
        return custom_agents.run_agent_now(
            agent_id, trigger="manual", business_id=ctx["business_id"],
        )
    except KeyError:
        raise HTTPException(404, "Custom agent not found")
