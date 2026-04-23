"""
Background agent scheduler — registers the autonomous agents with APScheduler.

Schedule (all times UTC):
    stale_deal_watcher  — daily at 08:30
    invoice_reminder    — daily at 09:00
    meeting_prep        — every 10 minutes during business hours

Activation:
    Call `start_agent_scheduler()` once at app boot. Idempotent — returns the
    existing scheduler on subsequent calls.
"""
from __future__ import annotations

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


def _safe_run(fn, label):
    try:
        fn()
    except Exception as e:
        logger.exception(f"[AgentScheduler] {label} failed")


def start_agent_scheduler():
    """Register jobs. Safe to call multiple times."""
    sched = _get_scheduler()
    if sched is None:
        return

    # Avoid duplicate registrations if reloaded
    existing_ids = {j.id for j in sched.get_jobs()}

    if "agent-stale-deal-watcher" not in existing_ids:
        from agents.background.stale_deal_watcher import run_for_all_businesses as stale_all
        from apscheduler.triggers.cron import CronTrigger
        sched.add_job(
            lambda: _safe_run(stale_all, "stale_deal_watcher"),
            CronTrigger(hour=8, minute=30),
            id="agent-stale-deal-watcher",
            replace_existing=True,
        )

    if "agent-invoice-reminder" not in existing_ids:
        from agents.background.invoice_reminder import run_for_all_businesses as inv_all
        from apscheduler.triggers.cron import CronTrigger
        sched.add_job(
            lambda: _safe_run(inv_all, "invoice_reminder"),
            CronTrigger(hour=9, minute=0),
            id="agent-invoice-reminder",
            replace_existing=True,
        )

    if "agent-meeting-prep" not in existing_ids:
        from agents.background.meeting_prep import run_for_all as meet_all
        from apscheduler.triggers.interval import IntervalTrigger
        sched.add_job(
            lambda: _safe_run(meet_all, "meeting_prep"),
            IntervalTrigger(minutes=10),
            id="agent-meeting-prep",
            replace_existing=True,
        )

    if "agent-memory-consolidate" not in existing_ids:
        from apscheduler.triggers.cron import CronTrigger
        def _run_memory_consolidate_all():
            from agents.summarizer import consolidate_business_memory
            from api.businesses import BUSINESSES_TABLE
            import sqlite3
            from config.settings import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    f"SELECT id FROM {BUSINESSES_TABLE} WHERE is_active = 1"
                ).fetchall()
            finally:
                conn.close()
            for r in rows:
                try:
                    consolidate_business_memory(r["id"], apply_changes=True)
                except Exception as e:
                    logger.warning(f"[AgentScheduler] memory_consolidate failed for {r['id']}: {e}")
        # Weekly, Sunday 03:00 UTC — low traffic
        sched.add_job(
            lambda: _safe_run(_run_memory_consolidate_all, "memory_consolidate"),
            CronTrigger(day_of_week="sun", hour=3, minute=0),
            id="agent-memory-consolidate",
            replace_existing=True,
        )

    if "agent-email-triage" not in existing_ids:
        from apscheduler.triggers.interval import IntervalTrigger
        def _run_email_triage_all():
            from agents.email_triage import run_for_business
            from api.businesses import BUSINESSES_TABLE
            import sqlite3
            from config.settings import DB_PATH
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            try:
                rows = conn.execute(
                    f"SELECT id FROM {BUSINESSES_TABLE} WHERE is_active = 1"
                ).fetchall()
            finally:
                conn.close()
            for r in rows:
                try:
                    run_for_business(r["id"])
                except Exception as e:
                    logger.warning(f"[AgentScheduler] email_triage failed for {r['id']}: {e}")
        sched.add_job(
            lambda: _safe_run(_run_email_triage_all, "email_triage"),
            IntervalTrigger(minutes=15),
            id="agent-email-triage",
            replace_existing=True,
        )

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
