"""Query History — stores every query with its result for search and re-run."""
from __future__ import annotations
import json, sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger
from config.settings import DB_PATH

TABLE = "nexus_query_history"

def _get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, query TEXT, intent TEXT,
        tools_used TEXT DEFAULT '[]', answer_preview TEXT, success INTEGER DEFAULT 1,
        duration_ms INTEGER DEFAULT 0, user_id TEXT DEFAULT 'default', starred INTEGER DEFAULT 0)""")
    conn.commit()
    return conn

def log_query(query, intent="unknown", tools_used=None, answer_preview="", success=True, duration_ms=0, user_id="default"):
    conn = _get_conn()
    cursor = conn.execute(f"INSERT INTO {TABLE} (timestamp,query,intent,tools_used,answer_preview,success,duration_ms,user_id) VALUES (?,?,?,?,?,?,?,?)",
        (datetime.now().isoformat(), query, intent, json.dumps(tools_used or []), answer_preview[:500], int(success), duration_ms, user_id))
    row_id = cursor.lastrowid; conn.commit(); conn.close()
    return row_id

def get_history(user_id="default", limit=50, search=None, intent_filter=None, starred_only=False):
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    parts = [f"SELECT * FROM {TABLE} WHERE user_id = ?"]; params = [user_id]
    if search: parts.append("AND (query LIKE ? OR answer_preview LIKE ?)"); params.extend([f"%{search}%", f"%{search}%"])
    if intent_filter: parts.append("AND intent = ?"); params.append(intent_filter)
    if starred_only: parts.append("AND starred = 1")
    parts.append("ORDER BY timestamp DESC LIMIT ?"); params.append(limit)
    rows = conn.execute(" ".join(parts), params).fetchall(); conn.close()
    return [{**dict(r), "tools_used": json.loads(r["tools_used"])} for r in rows]

def toggle_star(query_id):
    conn = _get_conn()
    conn.execute(f"UPDATE {TABLE} SET starred = CASE WHEN starred=1 THEN 0 ELSE 1 END WHERE id=?", (query_id,))
    conn.commit()
    row = conn.execute(f"SELECT starred FROM {TABLE} WHERE id=?", (query_id,)).fetchone()
    conn.close()
    return bool(row[0]) if row else False

def get_stats(user_id="default"):
    conn = _get_conn(); c = conn.cursor()
    c.execute(f"SELECT COUNT(*) FROM {TABLE} WHERE user_id=?", (user_id,)); total = c.fetchone()[0]
    c.execute(f"SELECT AVG(duration_ms) FROM {TABLE} WHERE user_id=?", (user_id,)); avg_time = round(c.fetchone()[0] or 0)
    c.execute(f"SELECT intent, COUNT(*) as cnt FROM {TABLE} WHERE user_id=? GROUP BY intent ORDER BY cnt DESC LIMIT 5", (user_id,))
    top_intents = [{"intent": r[0], "count": r[1]} for r in c.fetchall()]
    c.execute(f"SELECT AVG(success) FROM {TABLE} WHERE user_id=?", (user_id,)); sr = round((c.fetchone()[0] or 0) * 100, 1)
    conn.close()
    return {"total_queries": total, "avg_duration_ms": avg_time, "success_rate_pct": sr, "top_intents": top_intents}

def delete_query(query_id):
    conn = _get_conn(); conn.execute(f"DELETE FROM {TABLE} WHERE id=?", (query_id,)); conn.commit(); conn.close()

def clear_history(user_id="default"):
    conn = _get_conn(); cursor = conn.execute(f"DELETE FROM {TABLE} WHERE user_id=?", (user_id,)); count = cursor.rowcount; conn.commit(); conn.close()
    return count
