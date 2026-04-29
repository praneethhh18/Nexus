"""
Notification System — stores and serves notifications for the React UI.
Scoped per business so each tenant only sees its own alerts.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import List, Dict, Optional

from config.settings import DB_PATH

TABLE = "nexus_notifications"


def _ensure_column(conn, table, column, decl):
    cols = [r[1] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    if column not in cols:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")


def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
        id TEXT PRIMARY KEY,
        user_id TEXT DEFAULT 'default',
        business_id TEXT DEFAULT 'default',
        type TEXT,
        title TEXT,
        message TEXT,
        severity TEXT DEFAULT 'info',
        read INTEGER DEFAULT 0,
        created_at TEXT,
        metadata TEXT DEFAULT '{{}}'
    )""")
    _ensure_column(conn, TABLE, "business_id", "TEXT DEFAULT 'default'")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_notif_biz ON {TABLE}(business_id, created_at)")
    conn.commit()
    return conn


def push(
    title: str,
    message: str,
    type: str = "info",
    severity: str = "info",
    user_id: str = "default",
    business_id: str = "default",
    metadata: dict = None,
) -> str:
    """Push a notification scoped to a business. Returns notification ID."""
    nid = str(uuid.uuid4())[:10]
    conn = _get_conn()
    conn.execute(
        f"INSERT INTO {TABLE} (id, user_id, business_id, type, title, message, severity, created_at, metadata) "
        f"VALUES (?,?,?,?,?,?,?,?,?)",
        (nid, user_id, business_id, type, title, message, severity,
         datetime.now().isoformat(), json.dumps(metadata or {})),
    )
    conn.commit()
    conn.close()
    return nid


def get_recent(
    business_id: Optional[str] = None,
    user_id: str = "default",
    limit: int = 30,
    unread_only: bool = False,
) -> List[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    if business_id:
        query = f"SELECT * FROM {TABLE} WHERE business_id = ?"
        params: list = [business_id]
    else:
        query = f"SELECT * FROM {TABLE} WHERE user_id = ?"
        params = [user_id]
    if unread_only:
        query += " AND read = 0"
    query += " ORDER BY created_at DESC LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def mark_read(notification_id: str, business_id: Optional[str] = None):
    conn = _get_conn()
    if business_id:
        conn.execute(
            f"UPDATE {TABLE} SET read = 1 WHERE id = ? AND business_id = ?",
            (notification_id, business_id),
        )
    else:
        conn.execute(f"UPDATE {TABLE} SET read = 1 WHERE id = ?", (notification_id,))
    conn.commit()
    conn.close()


def mark_all_read(business_id: Optional[str] = None, user_id: str = "default"):
    conn = _get_conn()
    if business_id:
        conn.execute(f"UPDATE {TABLE} SET read = 1 WHERE business_id = ?", (business_id,))
    else:
        conn.execute(f"UPDATE {TABLE} SET read = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()


def get_unread_count(business_id: Optional[str] = None, user_id: str = "default") -> int:
    conn = _get_conn()
    if business_id:
        count = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE business_id = ? AND read = 0",
            (business_id,),
        ).fetchone()[0]
    else:
        count = conn.execute(
            f"SELECT COUNT(*) FROM {TABLE} WHERE user_id = ? AND read = 0",
            (user_id,),
        ).fetchone()[0]
    conn.close()
    return count


# ── Convenience pushers ──────────────────────────────────────────────────────
def notify_anomaly(region: str, drop_pct: float, user_id: str = "default", business_id: str = "default"):
    push(f"Anomaly: {region} Region", f"Revenue dropped {drop_pct:.1f}% below average",
         type="anomaly", severity="critical", user_id=user_id, business_id=business_id)


def notify_report_ready(filename: str, user_id: str = "default", business_id: str = "default"):
    push("Report Ready", f"PDF report generated: {filename}",
         type="report", severity="success", user_id=user_id, business_id=business_id)


def notify_workflow_complete(name: str, status: str, user_id: str = "default", business_id: str = "default"):
    sev = "success" if status == "success" else "warning"
    push(f"Workflow: {name}", f"Finished with status: {status}",
         type="workflow", severity=sev, user_id=user_id, business_id=business_id)


def notify_email_sent(to: str, subject: str, user_id: str = "default", business_id: str = "default"):
    push("Email Sent", f"To: {to} — {subject}",
         type="email", severity="info", user_id=user_id, business_id=business_id)
