"""
Conversation Store — persists chat sessions to SQLite.
Supports create, load, list, delete, and export of conversations.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger

from config.settings import DB_PATH

TABLE = "nexus_conversations"
MSG_TABLE = "nexus_conversation_messages"


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {TABLE} (
        conversation_id TEXT PRIMARY KEY,
        title TEXT,
        created_at TEXT,
        updated_at TEXT,
        message_count INTEGER DEFAULT 0,
        user_id TEXT DEFAULT 'default'
    )""")
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {MSG_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        conversation_id TEXT,
        role TEXT,
        content TEXT,
        tools_used TEXT DEFAULT '[]',
        citations TEXT DEFAULT '[]',
        sources_used TEXT DEFAULT '[]',
        multi_agent INTEGER DEFAULT 0,
        agents_used TEXT DEFAULT '[]',
        timestamp TEXT,
        FOREIGN KEY (conversation_id) REFERENCES {TABLE}(conversation_id)
    )""")
    conn.commit()
    return conn


def create_conversation(title: str = None, user_id: str = "default") -> str:
    """Create a new conversation. Returns conversation_id."""
    conv_id = str(uuid.uuid4())[:12]
    now = datetime.now().isoformat()
    if not title:
        title = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"

    conn = _get_conn()
    conn.execute(
        f"INSERT INTO {TABLE} (conversation_id, title, created_at, updated_at, message_count, user_id) "
        f"VALUES (?, ?, ?, ?, 0, ?)",
        (conv_id, title, now, now, user_id),
    )
    conn.commit()
    conn.close()
    logger.debug(f"[ConvStore] Created conversation: {conv_id} - {title}")
    return conv_id


def save_message(
    conversation_id: str,
    role: str,
    content: str,
    tools_used: list = None,
    citations: list = None,
    sources_used: list = None,
    multi_agent: bool = False,
    agents_used: list = None,
    timestamp: str = None,
) -> None:
    """Save a message to a conversation."""
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")

    conn = _get_conn()
    conn.execute(
        f"INSERT INTO {MSG_TABLE} "
        f"(conversation_id, role, content, tools_used, citations, sources_used, "
        f"multi_agent, agents_used, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            conversation_id,
            role,
            content,
            json.dumps(tools_used or []),
            json.dumps(citations or []),
            json.dumps(sources_used or []),
            int(multi_agent),
            json.dumps(agents_used or []),
            timestamp,
        ),
    )
    # Update conversation metadata
    conn.execute(
        f"UPDATE {TABLE} SET updated_at = ?, message_count = message_count + 1 "
        f"WHERE conversation_id = ?",
        (datetime.now().isoformat(), conversation_id),
    )
    conn.commit()
    conn.close()


def save_full_conversation(conversation_id: str, messages: list[dict]) -> None:
    """Save all messages for a conversation (replaces existing)."""
    conn = _get_conn()
    conn.execute(f"DELETE FROM {MSG_TABLE} WHERE conversation_id = ?", (conversation_id,))
    for msg in messages:
        conn.execute(
            f"INSERT INTO {MSG_TABLE} "
            f"(conversation_id, role, content, tools_used, citations, sources_used, "
            f"multi_agent, agents_used, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                conversation_id,
                msg.get("role", "user"),
                msg.get("content", ""),
                json.dumps(msg.get("tools_used", [])),
                json.dumps(msg.get("citations", [])),
                json.dumps(msg.get("sources_used", [])),
                int(msg.get("multi_agent", False)),
                json.dumps(msg.get("agents_used", [])),
                msg.get("timestamp", ""),
            ),
        )
    conn.execute(
        f"UPDATE {TABLE} SET updated_at = ?, message_count = ? WHERE conversation_id = ?",
        (datetime.now().isoformat(), len(messages), conversation_id),
    )
    conn.commit()
    conn.close()
    logger.debug(f"[ConvStore] Saved {len(messages)} messages to {conversation_id}")


def load_messages(conversation_id: str) -> list[dict]:
    """Load all messages for a conversation."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"SELECT * FROM {MSG_TABLE} WHERE conversation_id = ? ORDER BY id ASC",
        (conversation_id,),
    ).fetchall()
    conn.close()

    messages = []
    for row in rows:
        messages.append({
            "role": row["role"],
            "content": row["content"],
            "tools_used": json.loads(row["tools_used"]),
            "citations": json.loads(row["citations"]),
            "sources_used": json.loads(row["sources_used"]),
            "multi_agent": bool(row["multi_agent"]),
            "agents_used": json.loads(row["agents_used"]),
            "timestamp": row["timestamp"],
        })
    return messages


def list_conversations(user_id: str = "default", limit: int = 20) -> list[dict]:
    """List all conversations, most recent first."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        f"SELECT * FROM {TABLE} WHERE user_id = ? ORDER BY updated_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_title(conversation_id: str, title: str) -> None:
    """Update the title of a conversation."""
    conn = _get_conn()
    conn.execute(
        f"UPDATE {TABLE} SET title = ? WHERE conversation_id = ?",
        (title, conversation_id),
    )
    conn.commit()
    conn.close()


def auto_title(conversation_id: str, first_message: str) -> str:
    """Generate a title from the first user message."""
    title = first_message[:60].strip()
    if len(first_message) > 60:
        title += "..."
    update_title(conversation_id, title)
    return title


def delete_conversation(conversation_id: str) -> None:
    """Delete a conversation and all its messages."""
    conn = _get_conn()
    conn.execute(f"DELETE FROM {MSG_TABLE} WHERE conversation_id = ?", (conversation_id,))
    conn.execute(f"DELETE FROM {TABLE} WHERE conversation_id = ?", (conversation_id,))
    conn.commit()
    conn.close()
    logger.debug(f"[ConvStore] Deleted conversation: {conversation_id}")


def get_conversation_info(conversation_id: str) -> Optional[dict]:
    """Get metadata for a single conversation."""
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        f"SELECT * FROM {TABLE} WHERE conversation_id = ?",
        (conversation_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
