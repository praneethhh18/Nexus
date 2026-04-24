"""
Background agent scheduler — registers the autonomous agents with APScheduler.

Schedule (all times UTC):
    stale_deal_watcher  — daily at 08:30
    invoice_reminder    — daily at 09:00
    meeting_prep        — every 10 minutes during business hours
    morning_briefing    — daily at 08:00
    email_triage        — every 15 minutes
    memory_consolidate  — weekly, Sunday 03:00

Per-business controls:
    - Each business can disable an agent via the personas `enabled` flag.
      Disabled agents skip the run (recorded as 'skipped' in the run log).
    - Every run — success, skip, or failure — is written to `nexus_agent_runs`
      so the UI can show last-run status and error details without needing
      to scrape server logs.

Activation:
    Call `start_agent_scheduler()` once at app boot. Idempotent.
"""
from __future__ import annotations

from typing import Callable

from loguru import logger

_scheduler = None


def _get_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning("[AgentScheduler] APScheduler not installed — background agents disabled")
        return None
    _scheduler = BackgroundScheduler(timezone="UTC")
    _scheduler.start()
    logger.info("[AgentScheduler] Started")
    return _scheduler


# ── Per-business execution wrapper ──────────────────────────────────────────
def _is_enabled(business_id: str, agent_key: str) -> bool:
    """Honor the personas.enabled toggle — defaults to True if not set."""
    try:
        from agents.personas import get_persona
        return bool(get_persona(business_id, agent_key).get("enabled", True))
    except Exception:
        return True


def _iter_active_businesses():
    """Yield (id, name) for every active tenant. Never raises."""
    try:
        import sqlite3
        from api.businesses import BUSINESSES_TABLE
        from config.settings import DB_PATH
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                f"SELECT id, name FROM {BUSINESSES_TABLE} WHERE is_active = 1"
            ).fetchall()
        finally:
            conn.close()
        for r in rows:
            yield r["id"], r["name"]
    except Exception as e:
        logger.warning(f"[AgentScheduler] listing businesses failed: {e}")
        return


def _run_per_business(agent_key: str, runner: Callable[[str], dict | None]):
    """
    Iterate over active businesses, honor each one's enabled flag, and log the
    outcome (success / skipped / error) for every attempt.
    """
    from agents import run_log

    for bid, bname in _iter_active_businesses():
        if not _is_enabled(bid, agent_key):
            rid = run_log.start(bid, agent_key, trigger="scheduler")
            run_log.finish(rid, status="skipped", items_produced=0,
                           error="disabled by user")
            continue

        rid = run_log.start(bid, agent_key, trigger="scheduler")
        try:
            result = runner(bid) or {}
            items = _count_items(result)
            run_log.finish(rid, status="success", items_produced=items)
        except Exception as e:
            logger.exception(f"[AgentScheduler] {agent_key} failed for {bname}")
            run_log.finish(rid, status="error", error=str(e))


def _count_items(result: dict) -> int:
    """Best-effort extraction of 'how many things did this agent produce'."""
    if not isinstance(result, dict):
        return 0
    for k in ("queued", "created", "processed", "stale_deals",
              "candidates", "meetings", "consolidated", "count"):
        v = result.get(k)
        if isinstance(v, int):
            return v
    return 0


# ── Job registration ────────────────────────────────────────────────────────
def start_agent_scheduler():
    """Register jobs. Safe to call multiple times."""
    sched = _get_scheduler()
    if sched is None:
        return

    from apscheduler.triggers.cron import CronTrigger
    from apscheduler.triggers.interval import IntervalTrigger

    existing_ids = {j.id for j in sched.get_jobs()}

    def _register(job_id: str, trigger, runner_fn: Callable[[], None]):
        if job_id in existing_ids:
            return
        sched.add_job(runner_fn, trigger, id=job_id, replace_existing=True)

    # Stale-deal watcher — per business, daily 08:30
    def _stale_all():
        from agents.background.stale_deal_watcher import run_for_business
        _run_per_business("stale_deal_watcher", run_for_business)
    _register("agent-stale-deal-watcher", CronTrigger(hour=8, minute=30), _stale_all)

    # Invoice reminders — per business, daily 09:00
    def _invoice_all():
        from agents.background.invoice_reminder import run_for_business
        _run_per_business("invoice_reminder", run_for_business)
    _register("agent-invoice-reminder", CronTrigger(hour=9, minute=0), _invoice_all)

    # Meeting prep — uses its own per-user iteration, so we wrap it once.
    def _meeting_all():
        from agents import run_log
        from agents.background.meeting_prep import run_for_all
        # meeting_prep doesn't split by business yet — log as a single system run
        rid = run_log.start("__system__", "meeting_prep", trigger="scheduler")
        try:
            result = run_for_all() or {}
            run_log.finish(rid, status="success",
                           items_produced=_count_items(result))
        except Exception as e:
            logger.exception("[AgentScheduler] meeting_prep failed")
            run_log.finish(rid, status="error", error=str(e))
    _register("agent-meeting-prep", IntervalTrigger(minutes=10), _meeting_all)

    # Memory consolidation — weekly
    def _memory_all():
        from agents.summarizer import consolidate_business_memory
        def _runner(bid: str):
            return consolidate_business_memory(bid, apply_changes=True)
        _run_per_business("memory_consolidate", _runner)
    _register("agent-memory-consolidate",
              CronTrigger(day_of_week="sun", hour=3, minute=0), _memory_all)

    # Morning briefing — daily 08:00
    def _briefing_all():
        from agents.briefing import run_for_business
        _run_per_business("morning_briefing", run_for_business)
    _register("agent-morning-briefing", CronTrigger(hour=8, minute=0), _briefing_all)

    # Email triage — every 15 minutes
    def _triage_all():
        from agents.email_triage import run_for_business
        _run_per_business("email_triage", run_for_business)
    _register("agent-email-triage", IntervalTrigger(minutes=15), _triage_all)

    logger.info(f"[AgentScheduler] {len(sched.get_jobs())} jobs registered")


def list_jobs():
    sched = _get_scheduler()
    if sched is None:
        return []
    return [
        {
            "id": j.id,
            "next_run": j.next_run_time.isoformat() if j.next_run_time else None,
            "trigger": str(j.trigger),
        }
        for j in sched.get_jobs()
    ]


# ── Manual triggers (exposed via API) ────────────────────────────────────────
def run_stale_deal_watcher_now():
    from agents.background.stale_deal_watcher import run_for_all_businesses
    return run_for_all_businesses()


def run_invoice_reminder_now():
    from agents.background.invoice_reminder import run_for_all_businesses
    return run_for_all_businesses()


def run_meeting_prep_now():
    from agents.background.meeting_prep import run_for_all
    return run_for_all()


def run_briefing_now(business_id: str):
    from agents.briefing import run_for_business
    return run_for_business(business_id)
