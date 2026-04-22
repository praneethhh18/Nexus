"""
Audit Logger — records every tool call to JSON file and SQLite table.
Provides full traceability of all NexusAgent actions.
"""
from __future__ import annotations

import csv
import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger

from config.settings import AUDIT_LOG_PATH, DB_PATH, OUTPUTS_DIR

AUDIT_TABLE = "nexus_audit_log"


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {AUDIT_TABLE} (
        event_id TEXT PRIMARY KEY,
        timestamp TEXT,
        event_type TEXT DEFAULT 'tool_call',
        tool_name TEXT,
        input_summary TEXT,
        output_summary TEXT,
        duration_ms INTEGER,
        human_approved INTEGER DEFAULT 0,
        success INTEGER DEFAULT 1,
        error_message TEXT
    )""")
    conn.commit()
    return conn


def _append_json(entry: Dict[str, Any]) -> None:
    """Append a log entry to the JSON audit log file."""
    Path(OUTPUTS_DIR).mkdir(parents=True, exist_ok=True)
    log_path = Path(AUDIT_LOG_PATH)

    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
        except Exception:
            existing = []

    existing.append(entry)
    # Keep last 500 entries to prevent unbounded growth
    if len(existing) > 500:
        existing = existing[-500:]

    log_path.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def log_tool_call(
    tool: str,
    input_summary: str,
    output_summary: str,
    duration_ms: int = 0,
    approved: bool = True,
    success: bool = True,
    error: Optional[str] = None,
    event_type: str = "tool_call",
) -> str:
    """
    Log a tool call to both JSON and SQLite.
    Returns the event_id.
    """
    event_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()

    entry = {
        "event_id": event_id,
        "timestamp": timestamp,
        "event_type": event_type,
        "tool_name": tool,
        "input_summary": input_summary[:500],
        "output_summary": output_summary[:500],
        "duration_ms": duration_ms,
        "human_approved": approved,
        "success": success,
        "error_message": error or "",
    }

    # SQLite
    try:
        conn = _get_conn()
        conn.execute(f"""
        INSERT INTO {AUDIT_TABLE} VALUES (?,?,?,?,?,?,?,?,?,?)
        """, (
            event_id, timestamp, event_type, tool,
            entry["input_summary"], entry["output_summary"],
            duration_ms, int(approved), int(success), error or ""
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"[Audit] SQLite log failed: {e}")

    # JSON
    try:
        _append_json(entry)
    except Exception as e:
        logger.warning(f"[Audit] JSON log failed: {e}")

    logger.debug(f"[Audit] {tool}: success={success}, {duration_ms}ms")
    return event_id


def get_recent_logs(n: int = 20) -> List[Dict[str, Any]]:
    """Return the n most recent audit log entries."""
    try:
        conn = _get_conn()
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            f"SELECT * FROM {AUDIT_TABLE} ORDER BY timestamp DESC LIMIT ?", (n,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception:
        # Fallback to JSON
        log_path = Path(AUDIT_LOG_PATH)
        if log_path.exists():
            try:
                entries = json.loads(log_path.read_text(encoding="utf-8"))
                return entries[-n:][::-1]
            except Exception:
                pass
        return []


def get_stats() -> Dict[str, Any]:
    """Return aggregate audit statistics."""
    try:
        conn = _get_conn()
        c = conn.cursor()

        c.execute(f"SELECT COUNT(*) FROM {AUDIT_TABLE}")
        total = c.fetchone()[0]

        c.execute(f"SELECT AVG(success) FROM {AUDIT_TABLE}")
        success_rate = round((c.fetchone()[0] or 0) * 100, 1)

        c.execute(f"SELECT tool_name, COUNT(*) as cnt FROM {AUDIT_TABLE} GROUP BY tool_name ORDER BY cnt DESC LIMIT 1")
        top_row = c.fetchone()
        most_used = top_row[0] if top_row else "none"

        c.execute(f"SELECT AVG(duration_ms) FROM {AUDIT_TABLE}")
        avg_duration = round(c.fetchone()[0] or 0, 1)

        conn.close()
        return {
            "total_calls": total,
            "success_rate_pct": success_rate,
            "most_used_tool": most_used,
            "avg_duration_ms": avg_duration,
        }
    except Exception as e:
        logger.error(f"[Audit] get_stats failed: {e}")
        return {"total_calls": 0, "success_rate_pct": 0, "most_used_tool": "none", "avg_duration_ms": 0}


def export_csv(path: str) -> bool:
    """Export all audit logs to a CSV file."""
    try:
        logs = get_recent_logs(n=10000)
        if not logs:
            return False
        fieldnames = list(logs[0].keys())
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(logs)
        logger.info(f"[Audit] Exported {len(logs)} entries to {path}")
        return True
    except Exception as e:
        logger.error(f"[Audit] CSV export failed: {e}")
        return False
