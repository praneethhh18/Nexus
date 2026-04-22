"""
Query History — stores every query with its result for search and re-run.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger

from config.settings import DB_PATH

TABLE = "nexus_query_history"


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        query TEXT,
        intent TEXT,
        tools_used TEXT DEFAULT '[]',
        answer_preview TEXT,
        success INTEGER DEFAULT 1,
        duration_ms INTEGER DEFAULT 0,
        user_id TEXT DEFAULT 'default',
        starred INTEGER DEFAULT 0
    )""")
    conn.commit()
    return conn


def log_query(
    query: str,
    intent: str = "unknown",
    tools_used: list = None,
    answer_preview: str = "",
    success: bool = True,
    duration_ms: int = 0,
    user_id: str = "default",
) -> int:
    """Log a query to history. Returns the row id."""
    conn = _get_conn()
    cursor = conn.execute(
        f"INSERT INTO {TABLE} (timestamp, query, intent, tools_used, answer_preview, "
        f"success, duration_ms, user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (
            datetime.now().isoformat(),
            query,
            intent,
            json.dumps(tools_used or []),
            answer_preview[:500],
            int(success),
            duration_ms,
            user_id,
        ),
    )
    row_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return row_id


def get_history(
    user_id: str = "default",
    limit: int = 50,
    search: str = None,
    intent_filter: str = None,
    starred_only: bool = False,
) -> List[Dict[str, Any]]:
    """Get query history with optional filters."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row

    query_parts = [f"SELECT * FROM {TABLE} WHERE user_id = ?"]
    params: list = [user_id]

    if search:
        query_parts.append("AND (query LIKE ? OR answer_preview LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])

    if intent_filter:
        query_parts.append("AND intent = ?")
        params.append(intent_filter)

    if starred_only:
        query_parts.append("AND starred = 1")

    query_parts.append("ORDER BY timestamp DESC LIMIT ?")
    params.append(limit)

    sql = " ".join(query_parts)
    rows = conn.execute(sql, params).fetchall()
    conn.close()

    results = []
    for row in rows:
        r = dict(row)
        r["tools_used"] = json.loads(r["tools_used"])
        results.append(r)
    return results


def toggle_star(query_id: int) -> bool:
    """Toggle the starred status of a query. Returns new starred state."""
    conn = _get_conn()
    conn.execute(
        f"UPDATE {TABLE} SET starred = CASE WHEN starred = 1 THEN 0 ELSE 1 END WHERE id = ?",
        (query_id,),
    )
    conn.commit()
    row = conn.execute(f"SELECT starred FROM {TABLE} WHERE id = ?", (query_id,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False


def get_stats(user_id: str = "default") -> Dict[str, Any]:
    """Get query history statistics."""
    conn = _get_conn()
    c = conn.cursor()

    c.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE user_id = ?", (user_id,))
    total = c.fetchone()[0]

    c.execute(f"SELECT AVG(duration_ms) FROM {TABLE} WHERE user_id = ?", (user_id,))
    avg_time = round(c.fetchone()[0] or 0)

    c.execute(
        f"SELECT intent, COUNT(*) as cnt FROM {TABLE} WHERE user_id = ? "
        f"GROUP BY intent ORDER BY cnt DESC LIMIT 5",
        (user_id,),
    )
    top_intents = [{"intent": r[0], "count": r[1]} for r in c.fetchall()]

    c.execute(
        f"SELECT AVG(success) FROM {TABLE} WHERE user_id = ?",
        (user_id,),
    )
    success_rate = round((c.fetchone()[0] or 0) * 100, 1)

    conn.close()
    return {
        "total_queries": total,
        "avg_duration_ms": avg_time,
        "success_rate_pct": success_rate,
        "top_intents": top_intents,
    }


def delete_query(query_id: int) -> None:
    """Delete a single query from history."""
    conn = _get_conn()
    conn.execute(f"DELETE FROM {TABLE} WHERE id = ?", (query_id,))
    conn.commit()
    conn.close()


def clear_history(user_id: str = "default") -> int:
    """Clear all query history for a user. Returns count deleted."""
    conn = _get_conn()
    cursor = conn.execute(f"DELETE FROM {TABLE} WHERE user_id = ?", (user_id,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count
