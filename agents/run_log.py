"""
Agent run log — one row per scheduled or on-demand agent execution.

Gives the UI visible proof of what the autonomous team did, when, and whether
it succeeded. Purely local SQLite; no prompts or customer data are stored —
just agent_key, timestamps, status, a short items_produced count, and a
trimmed error message for failures.

Writers: agents/background/scheduler.py wraps every per-business run.
Readers: /api/agents/runs and the Agents page.
"""
from __future__ import annotations

import sqlite3  # only for sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from typing import Dict, List, Optional

from loguru import logger

from config.db import get_conn
from utils.timez import now_iso

TABLE = "nexus_agent_runs"

# Keep error strings bounded so a misbehaving agent can't blow up the DB.
_MAX_ERROR_CHARS = 800


def _conn():
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id              TEXT PRIMARY KEY,
            business_id     TEXT NOT NULL,
            agent_key       TEXT NOT NULL,
            trigger         TEXT NOT NULL,
            started_at      TEXT NOT NULL,
            finished_at     TEXT,
            status          TEXT NOT NULL,
            items_produced  INTEGER DEFAULT 0,
            error           TEXT
        )
    """)
    conn.execute(
        f"CREATE INDEX IF NOT EXISTS idx_{TABLE}_biz_agent_time "
        f"ON {TABLE}(business_id, agent_key, started_at DESC)"
    )
    return conn


def start(business_id: str, agent_key: str, trigger: str = "scheduler") -> str:
    """Record the start of a run; returns the run_id to pass to finish()."""
    run_id = uuid.uuid4().hex
    try:
        conn = _conn()
        try:
            conn.execute(
                f"INSERT INTO {TABLE} (id, business_id, agent_key, trigger, started_at, status) "
                f"VALUES (?, ?, ?, ?, ?, 'running')",
                (run_id, business_id, agent_key, trigger, now_iso()),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"[RunLog] start({agent_key}) failed: {e}")
    return run_id


def finish(
    run_id: str,
    status: str,
    items_produced: int = 0,
    error: Optional[str] = None,
) -> None:
    """Close a run. status ∈ {'success', 'skipped', 'error'}."""
    if status not in ("success", "skipped", "error"):
        status = "error"
    err = (error or "")[:_MAX_ERROR_CHARS] if error else None
    try:
        conn = _conn()
        try:
            conn.execute(
                f"UPDATE {TABLE} SET finished_at = ?, status = ?, "
                f"items_produced = ?, error = ? WHERE id = ?",
                (now_iso(), status, int(items_produced or 0), err, run_id),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.warning(f"[RunLog] finish({run_id}) failed: {e}")


def list_runs(
    business_id: str,
    agent_key: Optional[str] = None,
    limit: int = 50,
) -> List[Dict]:
    """Return recent runs, newest first."""
    limit = max(1, min(limit, 500))
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        if agent_key:
            rows = conn.execute(
                f"SELECT * FROM {TABLE} WHERE business_id = ? AND agent_key = ? "
                f"ORDER BY started_at DESC LIMIT ?",
                (business_id, agent_key, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                f"SELECT * FROM {TABLE} WHERE business_id = ? "
                f"ORDER BY started_at DESC LIMIT ?",
                (business_id, limit),
            ).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def last_run(business_id: str, agent_key: str) -> Optional[Dict]:
    """Most recent run for a single agent, or None."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? AND agent_key = ? "
            f"ORDER BY started_at DESC LIMIT 1",
            (business_id, agent_key),
        ).fetchone()
    finally:
        conn.close()
    return dict(row) if row else None


def summary(business_id: str, hours: int = 24) -> Dict[str, Dict]:
    """Per-agent counts in the last `hours` hours: {agent_key: {success, error, skipped}}."""
    # Compute cutoff in Python instead of using SQLite's datetime() — that
    # function doesn't exist on Postgres, where the rest of the app may run.
    from datetime import datetime, timedelta, timezone
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=int(hours))).isoformat()
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT agent_key, status, COUNT(*) AS n FROM {TABLE} "
            f"WHERE business_id = ? AND started_at > ? "
            f"GROUP BY agent_key, status",
            (business_id, cutoff),
        ).fetchall()
    finally:
        conn.close()
    out: Dict[str, Dict] = {}
    for r in rows:
        out.setdefault(r["agent_key"], {"success": 0, "error": 0, "skipped": 0})
        out[r["agent_key"]][r["status"]] = int(r["n"])
    return out
