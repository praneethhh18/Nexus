"""
Per-business agent schedule preferences.

The six built-in agents have sensible default cadences
(see `DEFAULT_INTERVALS_MIN` below), but every business can override them:
"email triage every 15 minutes" becomes "every hour" without touching code.

This module:
  * Declares the default interval per agent
  * Persists per-business overrides in `nexus_agent_schedule_prefs`
  * Exposes `effective_interval(business_id, agent_key)` for the scheduler

The scheduler itself reads prefs at boot; when a pref changes through the API,
the server calls `rebuild_custom_jobs()` in `agents.background.scheduler`.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, List

from config.settings import DB_PATH
from utils.timez import now_iso

TABLE = "nexus_agent_schedule_prefs"

# Default cadence in MINUTES for the built-in agents.
# Agents whose default is a cron (daily at 08:00) are represented as 1440
# minutes so the UI can still show "every 24 hours" and the user can tighten
# it without us growing a full cron picker yet.
DEFAULT_INTERVALS_MIN: Dict[str, int] = {
    "morning_briefing":    1440,   # daily
    "evening_digest":      1440,   # daily
    "email_triage":        15,
    "invoice_reminder":    1440,   # daily
    "stale_deal_watcher":  1440,   # daily
    "meeting_prep":        10,
    "memory_consolidate":  10080,  # weekly
}

# Clamp user choices into a sane range.
MIN_INTERVAL = 5        # 5 minutes
MAX_INTERVAL = 10080    # 1 week


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            business_id      TEXT NOT NULL,
            agent_key        TEXT NOT NULL,
            interval_minutes INTEGER NOT NULL,
            updated_at       TEXT NOT NULL,
            PRIMARY KEY (business_id, agent_key)
        )
    """)
    conn.commit()
    return conn


def _clamp(n) -> int:
    try:
        n = int(n)
    except (TypeError, ValueError):
        raise ValueError("interval_minutes must be an integer")
    if n < MIN_INTERVAL:
        raise ValueError(f"Interval too short (min {MIN_INTERVAL} min)")
    if n > MAX_INTERVAL:
        raise ValueError(f"Interval too long (max {MAX_INTERVAL} min)")
    return n


def get_overrides(business_id: str) -> Dict[str, int]:
    """Return {agent_key: interval_minutes} for every override set on this business."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT agent_key, interval_minutes FROM {TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return {r["agent_key"]: int(r["interval_minutes"]) for r in rows}


def effective_interval(business_id: str, agent_key: str) -> int:
    """Override if set, else the shipped default."""
    if agent_key not in DEFAULT_INTERVALS_MIN:
        raise ValueError(f"Unknown agent: {agent_key}")
    overrides = get_overrides(business_id)
    return overrides.get(agent_key, DEFAULT_INTERVALS_MIN[agent_key])


def set_interval(business_id: str, agent_key: str, interval_minutes: int) -> Dict:
    """Persist an override. Returns the effective value after save."""
    if agent_key not in DEFAULT_INTERVALS_MIN:
        raise ValueError(f"Unknown agent: {agent_key}")
    n = _clamp(interval_minutes)
    now = now_iso()
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {TABLE} (business_id, agent_key, interval_minutes, updated_at) "
            f"VALUES (?, ?, ?, ?) "
            f"ON CONFLICT(business_id, agent_key) DO UPDATE SET "
            f"interval_minutes = excluded.interval_minutes, "
            f"updated_at = excluded.updated_at",
            (business_id, agent_key, n, now),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "agent_key": agent_key,
        "interval_minutes": n,
        "default_minutes": DEFAULT_INTERVALS_MIN[agent_key],
        "is_custom": n != DEFAULT_INTERVALS_MIN[agent_key],
    }


def reset_interval(business_id: str, agent_key: str) -> Dict:
    """Remove the override — agent falls back to the shipped default."""
    if agent_key not in DEFAULT_INTERVALS_MIN:
        raise ValueError(f"Unknown agent: {agent_key}")
    conn = _conn()
    try:
        conn.execute(
            f"DELETE FROM {TABLE} WHERE business_id = ? AND agent_key = ?",
            (business_id, agent_key),
        )
        conn.commit()
    finally:
        conn.close()
    return {
        "agent_key": agent_key,
        "interval_minutes": DEFAULT_INTERVALS_MIN[agent_key],
        "default_minutes": DEFAULT_INTERVALS_MIN[agent_key],
        "is_custom": False,
    }


def list_schedule(business_id: str) -> List[Dict]:
    """Full list of built-in agents with their effective intervals — drives the UI."""
    overrides = get_overrides(business_id)
    out = []
    for key, default in DEFAULT_INTERVALS_MIN.items():
        current = overrides.get(key, default)
        out.append({
            "agent_key":        key,
            "interval_minutes": current,
            "default_minutes":  default,
            "is_custom":        current != default,
        })
    return out


# Presets the UI offers. A few round numbers, then 24 hours, then a week.
INTERVAL_PRESETS_MIN: List[int] = [5, 10, 15, 30, 60, 180, 360, 720, 1440, 4320, 10080]


def human_label(minutes: int) -> str:
    """Render an interval in the form '15 min' / '1 hr' / 'Daily' / 'Weekly'."""
    if minutes >= 10080 and minutes % 10080 == 0:
        weeks = minutes // 10080
        return "Weekly" if weeks == 1 else f"Every {weeks} weeks"
    if minutes >= 1440 and minutes % 1440 == 0:
        days = minutes // 1440
        return "Daily" if days == 1 else f"Every {days} days"
    if minutes >= 60 and minutes % 60 == 0:
        hours = minutes // 60
        return "Hourly" if hours == 1 else f"Every {hours} hr"
    return f"Every {minutes} min"
