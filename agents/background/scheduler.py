"""
Background agent scheduler — registers the autonomous agents with APScheduler.

Schedule (times in the configured scheduler timezone — see `_scheduler_tz`):
    stale_deal_watcher  — daily at 08:30
    invoice_reminder    — daily at 09:00
    meeting_prep        — every 10 minutes during business hours
    morning_briefing    — daily at 08:00
    evening_digest      — daily at 18:00
    email_triage        — every 15 minutes
    memory_consolidate  — weekly, Sunday 03:00

Timezone:
    Defaults to the system local timezone (so "08:00" means 08:00 wherever
    the server runs). Override with `SCHEDULER_TZ`, e.g. `SCHEDULER_TZ=UTC`
    or `SCHEDULER_TZ=America/Los_Angeles`. The chosen timezone is applied to
    BOTH the scheduler AND each CronTrigger explicitly — APScheduler 3.x
    triggers do NOT inherit the scheduler's timezone, which used to make
    the previous `timezone="UTC"` config silently ineffective.

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

import os
from typing import Callable

from loguru import logger

_scheduler = None


def _scheduler_tz():
    """
    Resolve the scheduler timezone. Honors SCHEDULER_TZ env var, otherwise
    defaults to system local. Returns a tzinfo-compatible object suitable
    for both BackgroundScheduler and CronTrigger.
    """
    name = (os.getenv("SCHEDULER_TZ") or "").strip()
    if name:
        try:
            from zoneinfo import ZoneInfo
            return ZoneInfo(name)
        except Exception as e:
            logger.warning(f"[AgentScheduler] SCHEDULER_TZ={name!r} invalid ({e}); falling back to local")
    try:
        from tzlocal import get_localzone
        return get_localzone()
    except Exception:
        from datetime import timezone
        return timezone.utc


def _get_scheduler():
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
    except ImportError:
        logger.warning("[AgentScheduler] APScheduler not installed — background agents disabled")
        return None
    tz = _scheduler_tz()
    _scheduler = BackgroundScheduler(timezone=tz)
    _scheduler.start()
    logger.info(f"[AgentScheduler] Started (timezone: {tz})")
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


def _interval_elapsed(business_id: str, agent_key: str) -> bool:
    """
    True if enough time has passed since this agent's last *successful* run for
    this business. Honors the per-business override configured in
    `api.agent_schedule`; falls back to the shipped default.

    Lets users tighten / loosen cadence from the UI without us spawning one
    APScheduler job per (business, agent) pair.
    """
    try:
        from api import agent_schedule
        from agents import run_log
        from datetime import datetime, timedelta, timezone

        minutes = agent_schedule.effective_interval(business_id, agent_key)
        last = run_log.last_run(business_id, agent_key)
        if not last or not last.get("started_at"):
            return True
        started = last["started_at"]
        try:
            d = datetime.fromisoformat(started.replace("Z", "+00:00"))
        except Exception:
            return True
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return (now - d) >= timedelta(minutes=minutes)
    except Exception:
        # Fail open — never block an agent because the pref lookup exploded.
        return True


def _run_per_business(agent_key: str, runner: Callable[[str], dict | None]):
    """
    Iterate over active businesses, honor each one's enabled flag + per-business
    interval override, and log the outcome (success / skipped / error) for every
    attempt that actually executed.
    """
    from agents import run_log

    for bid, bname in _iter_active_businesses():
        if not _is_enabled(bid, agent_key):
            rid = run_log.start(bid, agent_key, trigger="scheduler")
            run_log.finish(rid, status="skipped", items_produced=0,
                           error="disabled by user")
            continue

        if not _interval_elapsed(bid, agent_key):
            # Global job fires faster than this business's configured interval
            # — quietly skip without a run_log entry, otherwise the history view
            # fills up with no-op skips.
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

    tz = sched.timezone

    def _cron(**kw):
        # Always pin the trigger to the scheduler's timezone — APScheduler 3.x
        # CronTrigger picks up tzlocal at construction time otherwise.
        return CronTrigger(timezone=tz, **kw)

    existing_ids = {j.id for j in sched.get_jobs()}

    def _register(job_id: str, trigger, runner_fn: Callable[[], None]):
        if job_id in existing_ids:
            return
        sched.add_job(runner_fn, trigger, id=job_id, replace_existing=True)

    # Stale-deal watcher — per business, daily 08:30
    def _stale_all():
        from agents.background.stale_deal_watcher import run_for_business
        _run_per_business("stale_deal_watcher", run_for_business)
    _register("agent-stale-deal-watcher", _cron(hour=8, minute=30), _stale_all)

    # Invoice reminders — per business, daily 09:00
    def _invoice_all():
        from agents.background.invoice_reminder import run_for_business
        _run_per_business("invoice_reminder", run_for_business)
    _register("agent-invoice-reminder", _cron(hour=9, minute=0), _invoice_all)

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
              _cron(day_of_week="sun", hour=3, minute=0), _memory_all)

    # Morning briefing — daily 08:00 (scheduler tz)
    def _briefing_all():
        from agents.briefing import run_for_business
        _run_per_business("morning_briefing", run_for_business)
    _register("agent-morning-briefing", _cron(hour=8, minute=0), _briefing_all)

    # Evening digest — daily 18:00 (scheduler tz). The dashboard also auto-runs
    # after 4 PM local; this scheduler entry is the safety net for users who
    # don't open the app, ensuring the digest still gets generated and notified.
    def _evening_all():
        from agents.briefing import run_evening_for_business
        _run_per_business("evening_digest", run_evening_for_business)
    _register("agent-evening-digest", _cron(hour=18, minute=0), _evening_all)

    # Email triage — every 15 minutes
    def _triage_all():
        from agents.email_triage import run_for_business
        _run_per_business("email_triage", run_for_business)
    _register("agent-email-triage", IntervalTrigger(minutes=15), _triage_all)

    # Register user-defined custom agents from the DB
    try:
        rebuild_custom_jobs()
    except Exception as e:
        logger.warning(f"[AgentScheduler] rebuild_custom_jobs failed at boot: {e}")

    logger.info(f"[AgentScheduler] {len(sched.get_jobs())} jobs registered")


def rebuild_custom_jobs():
    """
    (Re)register every enabled custom agent from `nexus_custom_agents`.
    Called at boot and after any CRUD on a custom agent.

    Each custom agent gets its own APScheduler job so interval changes take
    effect immediately without restarting the process.
    """
    sched = _get_scheduler()
    if sched is None:
        return

    from apscheduler.triggers.interval import IntervalTrigger
    from api import custom_agents

    # Drop existing custom-* jobs so we can rebuild cleanly.
    for j in list(sched.get_jobs()):
        if j.id.startswith("custom-"):
            try:
                sched.remove_job(j.id)
            except Exception as e:
                logger.debug(f"[Scheduler] could not remove old custom job {j.id}: {e}")

    agents = custom_agents.list_all_enabled()
    for a in agents:
        job_id = f"custom-{a['id']}"
        interval_min = max(5, int(a.get("interval_minutes") or 60))
        def _make_runner(agent_id: str):
            def _runner():
                try:
                    custom_agents.run_agent_now(agent_id, trigger="scheduler")
                except Exception as e:
                    logger.exception(f"[AgentScheduler] custom agent {agent_id} failed")
            return _runner
        try:
            sched.add_job(
                _make_runner(a["id"]),
                IntervalTrigger(minutes=interval_min),
                id=job_id, replace_existing=True,
            )
        except Exception as e:
            logger.warning(f"[AgentScheduler] register custom agent {a['id']} failed: {e}")

    logger.info(f"[AgentScheduler] {len(agents)} custom agent job(s) active")


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


def run_evening_digest_now(business_id: str):
    from agents.briefing import run_evening_for_business
    return run_evening_for_business(business_id)
