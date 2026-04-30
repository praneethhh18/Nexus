"""
Conversation Store — persists chat sessions to SQLite, scoped per business.
Supports create, load, list, delete, and export of conversations.
"""
from __future__ import annotations

import json
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from datetime import datetime
from typing import Optional

from config.db import get_conn

TABLE = "nexus_conversations"
MSG_TABLE = "nexus_conversation_messages"


def _ensure_column(conn, table: str, column: str, decl: str) -> None:
    """Add a column to a table if it's missing. Safe to call on every boot.

    Backend-agnostic: tries the ALTER and swallows the duplicate-column error.
    Both SQLite and Postgres raise here when the column already exists; on
    Postgres we also need to rollback so the failed transaction doesn't poison
    later statements.
    """
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
        conversation_id TEXT PRIMARY KEY, title TEXT, created_at TEXT,
        updated_at TEXT, message_count INTEGER DEFAULT 0,
        user_id TEXT DEFAULT 'default',
        business_id TEXT DEFAULT 'default')""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {MSG_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT, role TEXT,
        content TEXT, tools_used TEXT DEFAULT '[]', citations TEXT DEFAULT '[]',
        sources_used TEXT DEFAULT '[]', multi_agent INTEGER DEFAULT 0,
        agents_used TEXT DEFAULT '[]', timestamp TEXT,
        FOREIGN KEY (conversation_id) REFERENCES {TABLE}(conversation_id))""")

    # Migrations: add business_id to existing installs
    _ensure_column(conn, TABLE, "business_id", "TEXT DEFAULT 'default'")
    # `sensitive=1` locks a conversation to local-only LLM regardless of
    # whether the cloud provider is configured. Off by default.
    _ensure_column(conn, TABLE, "sensitive", "INTEGER DEFAULT 0")

    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_conv_biz ON {TABLE}(business_id, updated_at)")
    conn.commit()
    return conn


def create_conversation(title=None, user_id="default", business_id="default"):
    conv_id = str(uuid.uuid4())[:12]
    now = datetime.now().isoformat()
    if not title:
        title = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"
    conn = _get_conn()
    conn.execute(
        f"INSERT INTO {TABLE} (conversation_id,title,created_at,updated_at,message_count,user_id,business_id) "
        f"VALUES (?,?,?,?,0,?,?)",
        (conv_id, title, now, now, user_id, business_id),
    )
    conn.commit()
    conn.close()
    return conv_id


def save_message(conversation_id, role, content, tools_used=None, citations=None,
                 sources_used=None, multi_agent=False, agents_used=None, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
    conn = _get_conn()
    conn.execute(
        f"INSERT INTO {MSG_TABLE} (conversation_id,role,content,tools_used,citations,sources_used,multi_agent,agents_used,timestamp) "
        f"VALUES (?,?,?,?,?,?,?,?,?)",
        (conversation_id, role, content, json.dumps(tools_used or []), json.dumps(citations or []),
         json.dumps(sources_used or []), int(multi_agent), json.dumps(agents_used or []), timestamp),
    )
    conn.execute(
        f"UPDATE {TABLE} SET updated_at=?, message_count=message_count+1 WHERE conversation_id=?",
        (datetime.now().isoformat(), conversation_id),
    )
    conn.commit()
    conn.close()


def save_full_conversation(conversation_id, messages):
    conn = _get_conn()
    conn.execute(f"DELETE FROM {MSG_TABLE} WHERE conversation_id=?", (conversation_id,))
    for msg in messages:
        conn.execute(
            f"INSERT INTO {MSG_TABLE} (conversation_id,role,content,tools_used,citations,sources_used,multi_agent,agents_used,timestamp) "
            f"VALUES (?,?,?,?,?,?,?,?,?)",
            (conversation_id, msg.get("role", "user"), msg.get("content", ""),
             json.dumps(msg.get("tools_used", [])), json.dumps(msg.get("citations", [])),
             json.dumps(msg.get("sources_used", [])), int(msg.get("multi_agent", False)),
             json.dumps(msg.get("agents_used", [])), msg.get("timestamp", "")),
        )
    conn.execute(
        f"UPDATE {TABLE} SET updated_at=?, message_count=? WHERE conversation_id=?",
        (datetime.now().isoformat(), len(messages), conversation_id),
    )
    conn.commit()
    conn.close()


def load_messages(conversation_id):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"SELECT * FROM {MSG_TABLE} WHERE conversation_id=? ORDER BY id ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"], "tools_used": json.loads(r["tools_used"]),
             "citations": json.loads(r["citations"]), "sources_used": json.loads(r["sources_used"]),
             "multi_agent": bool(r["multi_agent"]), "agents_used": json.loads(r["agents_used"]),
             "timestamp": r["timestamp"]} for r in rows]


def list_conversations(business_id: Optional[str] = None, user_id: str = "default", limit: int = 20):
    """
    List conversations for a business. If business_id is provided, only that business's
    conversations are returned. Legacy callers passing just user_id still work.
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    if business_id:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id=? ORDER BY updated_at DESC LIMIT ?",
            (business_id, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            f"SELECT * FROM {TABLE} WHERE user_id=? ORDER BY updated_at DESC LIMIT ?",
            (user_id, limit),
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_title(conversation_id, title):
    conn = _get_conn()
    conn.execute(f"UPDATE {TABLE} SET title=? WHERE conversation_id=?", (title, conversation_id))
    conn.commit()
    conn.close()


def set_sensitive(conversation_id: str, value: bool) -> None:
    """Toggle the local-only lock on a conversation."""
    conn = _get_conn()
    conn.execute(
        f"UPDATE {TABLE} SET sensitive=? WHERE conversation_id=?",
        (1 if value else 0, conversation_id),
    )
    conn.commit()
    conn.close()


def is_sensitive(conversation_id: str) -> bool:
    """True if the conversation is locked to local-only LLM."""
    info = get_conversation_info(conversation_id)
    return bool(info and info.get("sensitive"))


def auto_title(conversation_id, first_message):
    title = first_message[:60].strip()
    if len(first_message) > 60:
        title += "..."
    update_title(conversation_id, title)
    return title


def delete_conversation(conversation_id):
    conn = _get_conn()
    conn.execute(f"DELETE FROM {MSG_TABLE} WHERE conversation_id=?", (conversation_id,))
    conn.execute(f"DELETE FROM {TABLE} WHERE conversation_id=?", (conversation_id,))
    conn.commit()
    conn.close()


def get_conversation_info(conversation_id):
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute(f"SELECT * FROM {TABLE} WHERE conversation_id=?", (conversation_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def assert_conversation_access(conversation_id: str, business_id: str) -> dict:
    """Fetch conversation and verify it belongs to the given business. Raise on mismatch."""
    info = get_conversation_info(conversation_id)
    if not info:
        from fastapi import HTTPException
        raise HTTPException(404, "Conversation not found")
    if info.get("business_id") not in (business_id, "default"):
        from fastapi import HTTPException
        raise HTTPException(403, "Conversation belongs to a different business")
    return info
