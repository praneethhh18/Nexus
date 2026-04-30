"""Query History — stores every query with its result for search and re-run."""
from __future__ import annotations
import json
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import datetime
from typing import Optional
from config.db import get_conn

TABLE = "nexus_query_history"


def _ensure_column(conn, table, column, decl):
    """Add a column if missing. Try-and-ignore works on both SQLite and Postgres."""
    try:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {decl}")
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            pass


def _get_conn():
    conn = get_conn()
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, query TEXT, intent TEXT,
        tools_used TEXT DEFAULT '[]', answer_preview TEXT, success INTEGER DEFAULT 1,
        duration_ms INTEGER DEFAULT 0, user_id TEXT DEFAULT 'default',
        business_id TEXT DEFAULT 'default', starred INTEGER DEFAULT 0)""")
    _ensure_column(conn, TABLE, "business_id", "TEXT DEFAULT 'default'")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_qh_biz ON {TABLE}(business_id, timestamp)")
    conn.commit()
    return conn


def log_query(query, intent="unknown", tools_used=None, answer_preview="",
              success=True, duration_ms=0, user_id="default", business_id="default"):
    conn = _get_conn()
    # RETURNING id is portable across SQLite (3.35+) and Postgres — replaces
    # cursor.lastrowid which doesn't work on the Postgres wrapper.
    cursor = conn.execute(
        f"INSERT INTO {TABLE} (timestamp,query,intent,tools_used,answer_preview,success,duration_ms,user_id,business_id) "
        f"VALUES (?,?,?,?,?,?,?,?,?) RETURNING id",
        (datetime.now().isoformat(), query, intent, json.dumps(tools_used or []),
         answer_preview[:500], int(success), duration_ms, user_id, business_id),
    )
    row_id = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return row_id


def get_history(business_id: Optional[str] = None, user_id: str = "default", limit: int = 50,
                search: Optional[str] = None, intent_filter: Optional[str] = None,
                starred_only: bool = False):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    if business_id:
        parts = [f"SELECT * FROM {TABLE} WHERE business_id = ?"]
        params: list = [business_id]
    else:
        parts = [f"SELECT * FROM {TABLE} WHERE user_id = ?"]
        params = [user_id]
    if search:
        parts.append("AND (query LIKE ? OR answer_preview LIKE ?)")
        params.extend([f"%{search}%", f"%{search}%"])
    if intent_filter:
        parts.append("AND intent = ?")
        params.append(intent_filter)
    if starred_only:
        parts.append("AND starred = 1")
    parts.append("ORDER BY timestamp DESC LIMIT ?")
    params.append(limit)
    rows = conn.execute(" ".join(parts), params).fetchall()
    conn.close()
    return [{**dict(r), "tools_used": json.loads(r["tools_used"])} for r in rows]


def toggle_star(query_id):
    conn = _get_conn()
    conn.execute(f"UPDATE {TABLE} SET starred = CASE WHEN starred=1 THEN 0 ELSE 1 END WHERE id=?", (query_id,))
    conn.commit()
    row = conn.execute(f"SELECT starred FROM {TABLE} WHERE id=?", (query_id,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False


def get_stats(business_id: Optional[str] = None, user_id: str = "default"):
    conn = _get_conn()
    c = conn.cursor()
    if business_id:
        where = "WHERE business_id = ?"
        params = (business_id,)
    else:
        where = "WHERE user_id = ?"
        params = (user_id,)
    c.execute(f"SELECT COUNT(*) FROM {TABLE} {where}", params)
    total = c.fetchone()[0]
    c.execute(f"SELECT AVG(duration_ms) FROM {TABLE} {where}", params)
    avg_time = round(c.fetchone()[0] or 0)
    c.execute(
        f"SELECT intent, COUNT(*) as cnt FROM {TABLE} {where} GROUP BY intent ORDER BY cnt DESC LIMIT 5",
        params,
    )
    top_intents = [{"intent": r[0], "count": r[1]} for r in c.fetchall()]
    c.execute(f"SELECT AVG(success) FROM {TABLE} {where}", params)
    sr = round((c.fetchone()[0] or 0) * 100, 1)
    conn.close()
    return {"total_queries": total, "avg_duration_ms": avg_time, "success_rate_pct": sr, "top_intents": top_intents}


def delete_query(query_id):
    conn = _get_conn()
    conn.execute(f"DELETE FROM {TABLE} WHERE id=?", (query_id,))
    conn.commit()
    conn.close()


def clear_history(business_id: Optional[str] = None, user_id: str = "default"):
    conn = _get_conn()
    if business_id:
        cursor = conn.execute(f"DELETE FROM {TABLE} WHERE business_id=?", (business_id,))
    else:
        cursor = conn.execute(f"DELETE FROM {TABLE} WHERE user_id=?", (user_id,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count
