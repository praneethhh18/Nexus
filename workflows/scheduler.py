"""
Workflow Scheduler — APScheduler integration.
Only enabled workflows with schedule_trigger are registered.
Re-syncs on workflow enable/disable.
"""
from __future__ import annotations

import threading
from datetime import datetime
from typing import Dict, Any, Optional
from loguru import logger

_scheduler = None
_lock = threading.Lock()
_run_history: list = []   # last 50 run summaries (in-memory)


def _get_scheduler():
    global _scheduler
    if _scheduler is None:
        from apscheduler.schedulers.background import BackgroundScheduler
        _scheduler = BackgroundScheduler(timezone="UTC")
        _scheduler.start()
        logger.info("[WFScheduler] APScheduler started")
    return _scheduler


def _run_workflow_job(wf_id: str):
    """APScheduler job function — load and execute a workflow."""
    from workflows.storage import load_workflow
    from workflows.executor import execute_workflow

    wf = load_workflow(wf_id)
    if not wf or not wf.get("enabled"):
        return

    logger.info(f"[WFScheduler] Scheduled run: '{wf.get('name')}' ({wf_id})")
    try:
        result = execute_workflow(wf)
        _run_history.append({
            "workflow_name": wf.get("name"),
            "workflow_id": wf_id,
            "run_id": result.get("run_id"),
            "status": result.get("status"),
            "finished_at": result.get("finished_at"),
            "duration_ms": result.get("duration_ms"),
        })
        # Keep last 50
        if len(_run_history) > 50:
            _run_history.pop(0)
    except Exception as e:
        logger.error(f"[WFScheduler] Run failed for {wf_id}: {e}")


def _parse_schedule(trigger_node: dict) -> Optional[dict]:
    """Convert trigger config to APScheduler trigger kwargs."""
    config = trigger_node.get("config", {})
    mode = config.get("mode", "daily")

    if mode == "interval":
        minutes = int(config.get("interval_minutes", 60))
        return {"trigger": "interval", "minutes": minutes}

    elif mode == "cron":
        expr = config.get("cron_expression", "0 8 * * *").split()
        if len(expr) == 5:
            minute, hour, day, month, day_of_week = expr
            return {
                "trigger": "cron",
                "minute": minute, "hour": hour,
                "day": day, "month": month, "day_of_week": day_of_week,
            }

    elif mode == "daily":
        time_str = config.get("daily_time", "08:00")
        h, m = time_str.split(":") if ":" in time_str else ("8", "0")
        return {"trigger": "cron", "hour": int(h), "minute": int(m)}

    elif mode == "weekly":
        day_map = {
            "Monday": "mon", "Tuesday": "tue", "Wednesday": "wed",
            "Thursday": "thu", "Friday": "fri", "Saturday": "sat", "Sunday": "sun",
        }
        day = day_map.get(config.get("weekly_day", "Monday"), "mon")
        time_str = config.get("weekly_time", "09:00")
        h, m = time_str.split(":") if ":" in time_str else ("9", "0")
        return {"trigger": "cron", "day_of_week": day, "hour": int(h), "minute": int(m)}

    return None


def sync_all_workflows():
    """Register/unregister APScheduler jobs for all enabled workflows."""
    with _lock:
        try:
            from workflows.storage import list_workflows
            scheduler = _get_scheduler()

            # Remove all existing workflow jobs
            for job in scheduler.get_jobs():
                if job.id.startswith("wf-"):
                    scheduler.remove_job(job.id)

            registered = 0
            for wf in list_workflows():
                if not wf.get("enabled"):
                    continue
                # Find the schedule trigger node
                trigger_node = next(
                    (n for n in wf.get("nodes", []) if n.get("type") == "schedule_trigger"),
                    None
                )
                if not trigger_node:
                    continue

                schedule_kwargs = _parse_schedule(trigger_node)
                if not schedule_kwargs:
                    continue

                trigger_type = schedule_kwargs.pop("trigger")
                try:
                    scheduler.add_job(
                        _run_workflow_job,
                        trigger=trigger_type,
                        kwargs={"wf_id": wf["id"]},
                        id=wf["id"],
                        replace_existing=True,
                        **schedule_kwargs,
                    )
                    registered += 1
                    logger.info(f"[WFScheduler] Registered: '{wf['name']}' ({trigger_type})")
                except Exception as e:
                    logger.warning(f"[WFScheduler] Failed to register '{wf['name']}': {e}")

            logger.info(f"[WFScheduler] Sync complete: {registered} workflows scheduled")
        except Exception as e:
            logger.error(f"[WFScheduler] sync_all_workflows error: {e}")


def register_workflow(wf_id: str):
    """Register a single workflow (called after enabling)."""
    sync_all_workflows()


def unregister_workflow(wf_id: str):
    """Remove a workflow from the scheduler."""
    with _lock:
        try:
            scheduler = _get_scheduler()
            if scheduler.get_job(wf_id):
                scheduler.remove_job(wf_id)
                logger.info(f"[WFScheduler] Unregistered: {wf_id}")
        except Exception as e:
            logger.warning(f"[WFScheduler] Unregister failed: {e}")


def get_scheduled_jobs() -> list:
    try:
        scheduler = _get_scheduler()
        return [
            {
                "id": job.id,
                "next_run": str(job.next_run_time) if job.next_run_time else "N/A",
                "trigger": str(job.trigger),
            }
            for job in scheduler.get_jobs()
        ]
    except Exception:
        return []


def get_run_history(n: int = 20) -> list:
    return _run_history[-n:][::-1]
