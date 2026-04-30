"""
Proactive nudges — your AI team raising a hand when they notice something.

A nudge is a small, actionable suggestion surfaced on the Dashboard:
    "Kira noticed 2 overdue invoices. Draft reminders? [Accept] [Later]"

Each detector runs quickly against local SQLite. No LLM calls here —
nudges need to be instant. The LLM work happens *after* the user accepts,
by triggering the corresponding agent.

Dismissed nudges stay hidden until the next calendar day (UTC). This way
the user isn't nagged about the same thing repeatedly but the nudge comes
back tomorrow if still relevant.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from agents.personas import get_persona
from config.db import get_conn
from utils.timez import now_utc_naive

DISMISS_TABLE = "nexus_nudge_dismissals"


# ── Storage ─────────────────────────────────────────────────────────────────
def _get_conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {DISMISS_TABLE} (
            business_id TEXT NOT NULL,
            nudge_id    TEXT NOT NULL,
            dismissed_on TEXT NOT NULL,          -- ISO date, UTC
            PRIMARY KEY (business_id, nudge_id, dismissed_on)
        )
    """)
    conn.commit()
    return conn


def _is_dismissed(business_id: str, nudge_id: str) -> bool:
    """Check if this nudge has been dismissed today (UTC)."""
    today = date.today().isoformat()
    conn = _get_conn()
    try:
        row = conn.execute(
            f"SELECT 1 FROM {DISMISS_TABLE} "
            f"WHERE business_id = ? AND nudge_id = ? AND dismissed_on = ?",
            (business_id, nudge_id, today),
        ).fetchone()
    finally:
        conn.close()
    return bool(row)


def dismiss(business_id: str, nudge_id: str) -> None:
    """Hide this nudge for the rest of the current UTC day."""
    today = date.today().isoformat()
    conn = _get_conn()
    try:
        # Portable: ON CONFLICT works on SQLite 3.24+ and Postgres.
        conn.execute(
            f"INSERT INTO {DISMISS_TABLE} (business_id, nudge_id, dismissed_on) "
            f"VALUES (?, ?, ?) "
            f"ON CONFLICT (business_id, nudge_id, dismissed_on) DO NOTHING",
            (business_id, nudge_id, today),
        )
        conn.commit()
    finally:
        conn.close()


# ── Detectors — one per agent ───────────────────────────────────────────────
# Each returns either a nudge dict or None.


def _nudge_invoice_reminder(business_id: str) -> Optional[Dict]:
    """Kira: overdue invoices without a draft reminder in the queue already."""
    try:
        today = date.today().isoformat()
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            # Overdue, not paid, no pending reminder in the last 7 days
            rows = conn.execute(
                "SELECT id, customer_name, total, currency, due_date "
                "FROM nexus_invoices "
                "WHERE business_id = ? AND status != 'paid' "
                "AND due_date IS NOT NULL AND due_date < ? "
                "ORDER BY due_date ASC",
                (business_id, today),
            ).fetchall()
        finally: conn.close()
    except Exception as e:
        logger.debug(f"[Nudges] invoice lookup: {e}")
        return None

    if not rows:
        return None

    # Filter to invoices without a recent reminder approval
    pending = []
    cutoff = (now_utc_naive() - timedelta(days=7)).isoformat()
    conn = get_conn()
    try:
        for r in rows:
            dup = conn.execute(
                "SELECT 1 FROM nexus_agent_approvals "
                "WHERE business_id = ? AND tool_name = 'send_invoice_email' "
                "AND args_json LIKE ? AND created_at > ? LIMIT 1",
                (business_id, f'%"invoice_id": "{r["id"]}"%', cutoff),
            ).fetchone()
            if not dup:
                pending.append(dict(r))
    finally:
        conn.close()

    if not pending:
        return None

    count = len(pending)
    top = pending[0]
    detail_bits = [
        f"{top['customer_name']} · {top['currency'] or 'INR'} {int(float(top['total'] or 0)):,}"
    ]
    if count > 1:
        detail_bits.append(f"+{count - 1} more")

    return {
        "id":        "kira.overdue_invoices",
        "agent_key": "invoice_reminder",
        "title":     f"{count} overdue invoice{'s' if count != 1 else ''} need a nudge",
        "detail":    " · ".join(detail_bits),
        "cta_label": "Draft reminder emails",
        "action":    {"kind": "run_agent", "agent_key": "invoice_reminder"},
        "priority":  80,
    }


def _nudge_stale_deals(business_id: str) -> Optional[Dict]:
    """Arjun: deals that haven't moved in 14+ days."""
    try:
        cutoff = (now_utc_naive() - timedelta(days=14)).isoformat()
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            rows = conn.execute(
                "SELECT id, name, stage, updated_at FROM nexus_deals "
                "WHERE business_id = ? AND stage NOT IN ('won', 'lost') "
                "AND (updated_at IS NULL OR updated_at < ?) "
                "ORDER BY updated_at ASC NULLS FIRST LIMIT 20",
                (business_id, cutoff),
            ).fetchall()
        finally: conn.close()
    except Exception as e:
        logger.debug(f"[Nudges] stale deals lookup: {e}")
        return None

    if not rows:
        return None

    count = len(rows)
    top = rows[0]
    return {
        "id":        "arjun.stale_deals",
        "agent_key": "stale_deal_watcher",
        "title":     f"{count} deal{'s' if count != 1 else ''} stuck for 2+ weeks",
        "detail":    f"{top['name']} ({top['stage']}){' · +'+str(count-1)+' more' if count > 1 else ''}",
        "cta_label": "Create follow-up tasks",
        "action":    {"kind": "run_agent", "agent_key": "stale_deal_watcher"},
        "priority":  70,
    }


def _nudge_email_triage(business_id: str) -> Optional[Dict]:
    """Iris: drafts waiting in the approval queue from her last triage run."""
    try:
        cutoff = (now_utc_naive() - timedelta(hours=24)).isoformat()
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM nexus_agent_approvals "
                "WHERE business_id = ? AND status = 'pending' "
                "AND tool_name IN ('send_triage_reply', 'draft_reply', 'classify_and_reply') "
                "AND created_at > ?",
                (business_id, cutoff),
            ).fetchone()
        finally: conn.close()
    except Exception as e:
        logger.debug(f"[Nudges] triage lookup: {e}")
        return None

    n = int(row["n"] if row else 0)
    if n == 0:
        return None
    return {
        "id":        "iris.pending_drafts",
        "agent_key": "email_triage",
        "title":     f"{n} email draft{'s' if n != 1 else ''} waiting for your review",
        "detail":    "Iris classified them — you just need to approve, edit, or skip.",
        "cta_label": "Review drafts",
        "action":    {"kind": "navigate", "path": "/approvals"},
        "priority":  60,
    }


def _nudge_morning_briefing(business_id: str) -> Optional[Dict]:
    """Atlas: no briefing yet today."""
    try:
        today = date.today().isoformat()
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM nexus_briefings "
                "WHERE business_id = ? AND DATE(created_at) = ?",
                (business_id, today),
            ).fetchone()
        finally: conn.close()
    except Exception:
        return None

    if int(row["n"] if row else 0) > 0:
        return None

    # Only suggest a briefing if there's any business data to brief on
    try:
        conn = get_conn()
        try:
            cnt = conn.execute(
                "SELECT "
                "(SELECT COUNT(*) FROM nexus_tasks WHERE business_id = ? AND status != 'done') + "
                "(SELECT COUNT(*) FROM nexus_invoices WHERE business_id = ? AND status != 'paid') + "
                "(SELECT COUNT(*) FROM nexus_deals WHERE business_id = ? AND stage NOT IN ('won','lost')) "
                "AS total",
                (business_id, business_id, business_id),
            ).fetchone()[0]
        finally: conn.close()
    except Exception:
        cnt = 0
    if not cnt:
        return None

    return {
        "id":        "atlas.todays_briefing",
        "agent_key": "morning_briefing",
        "title":     "Today's briefing isn't ready yet",
        "detail":    "A 1-page summary of tasks, invoices, and pipeline in ~2 seconds.",
        "cta_label": "Generate briefing",
        "action":    {"kind": "run_agent", "agent_key": "morning_briefing"},
        "priority":  90,
    }


def _nudge_meeting_prep(business_id: str) -> Optional[Dict]:
    """Sage: upcoming meetings in the next 2 hours."""
    try:
        now = now_utc_naive()
        cutoff = (now + timedelta(hours=2)).isoformat()
        conn = get_conn(); conn.row_factory = sqlite3.Row
        try:
            row = conn.execute(
                "SELECT COUNT(*) AS n FROM nexus_calendar_events "
                "WHERE business_id = ? AND start_ts >= ? AND start_ts <= ?",
                (business_id, now.isoformat(), cutoff),
            ).fetchone()
        finally: conn.close()
    except Exception:
        return None

    n = int(row["n"] if row else 0)
    if n == 0:
        return None
    return {
        "id":        "sage.upcoming_meetings",
        "agent_key": "meeting_prep",
        "title":     f"{n} meeting{'s' if n != 1 else ''} in the next 2 hours",
        "detail":    "Sage can generate briefs on the contacts involved.",
        "cta_label": "Prepare briefs",
        "action":    {"kind": "run_agent", "agent_key": "meeting_prep"},
        "priority":  95,
    }


DETECTORS = [
    _nudge_morning_briefing,   # Atlas
    _nudge_invoice_reminder,   # Kira
    _nudge_stale_deals,        # Arjun
    _nudge_email_triage,       # Iris
    _nudge_meeting_prep,       # Sage
    # Echo (memory_consolidate) doesn't emit nudges — it's a weekly silent agent.
]


# ── Public API ──────────────────────────────────────────────────────────────
def list_active(business_id: str) -> List[Dict]:
    """
    Return all active nudges for this business, newest-priority first.
    Dismissed nudges are filtered out (re-appear tomorrow UTC).
    """
    nudges: List[Dict] = []
    for fn in DETECTORS:
        try:
            n = fn(business_id)
        except Exception as e:
            logger.warning(f"[Nudges] {fn.__name__} failed: {e}")
            continue
        if not n:
            continue
        if _is_dismissed(business_id, n["id"]):
            continue
        # Attach resolved persona
        p = get_persona(business_id, n["agent_key"])
        n["agent_name"]     = p["name"]
        n["agent_role_tag"] = p["role_tag"]
        n["agent_emoji"]    = p["emoji"]
        nudges.append(n)

    nudges.sort(key=lambda x: -x.get("priority", 0))
    return nudges
