"""
Notification preferences — per-user toggles controlling which events become
bell entries.

Keeps the UX honest: users who don't want "agent_completed" chatter can mute
it without losing "approval_waiting" alerts. Absence of a row means "use the
shipped defaults" — safe for existing accounts.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict

from config.settings import DB_PATH

TABLE = "nexus_notification_prefs"

# Event types the system knows about and their defaults. New event types
# should be added here so the prefs page auto-lists them.
DEFAULTS: Dict[str, bool] = {
    "agent_completed":    True,
    "approval_waiting":   True,
    "anomaly_detected":   True,
    "invoice_overdue":    True,
    "meeting_soon":       True,
    "document_processed": True,
    "workflow_completed": True,
    "email_sent":         False,   # quieter by default — can get noisy
}


def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            user_id     TEXT NOT NULL,
            event_type  TEXT NOT NULL,
            enabled     INTEGER NOT NULL DEFAULT 1,
            updated_at  TEXT NOT NULL,
            PRIMARY KEY (user_id, event_type)
        )
    """)
    conn.commit()
    return conn


def get_prefs(user_id: str) -> Dict[str, bool]:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT event_type, enabled FROM {TABLE} WHERE user_id = ?",
            (user_id,),
        ).fetchall()
    finally:
        conn.close()
    overrides = {r["event_type"]: bool(r["enabled"]) for r in rows}
    return {k: overrides.get(k, v) for k, v in DEFAULTS.items()}


def set_prefs(user_id: str, updates: Dict[str, bool]) -> Dict[str, bool]:
    """Merge partial updates. Unknown event types are ignored."""
    now = datetime.utcnow().isoformat()
    clean = {k: bool(v) for k, v in (updates or {}).items() if k in DEFAULTS}
    if not clean:
        return get_prefs(user_id)
    conn = _conn()
    try:
        for event_type, enabled in clean.items():
            conn.execute(
                f"INSERT INTO {TABLE} (user_id, event_type, enabled, updated_at) "
                f"VALUES (?, ?, ?, ?) "
                f"ON CONFLICT(user_id, event_type) DO UPDATE SET "
                f"enabled = excluded.enabled, updated_at = excluded.updated_at",
                (user_id, event_type, 1 if enabled else 0, now),
            )
        conn.commit()
    finally:
        conn.close()
    return get_prefs(user_id)


def should_send(user_id: str, event_type: str) -> bool:
    """Check before calling `notifications.push(...)` from any agent code."""
    return get_prefs(user_id).get(event_type, DEFAULTS.get(event_type, True))
