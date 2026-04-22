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
from typing import Optional

from loguru import logger
from config.settings import DB_PATH

TABLE = "nexus_conversations"
MSG_TABLE = "nexus_conversation_messages"

def _get_conn():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
        conversation_id TEXT PRIMARY KEY, title TEXT, created_at TEXT,
        updated_at TEXT, message_count INTEGER DEFAULT 0, user_id TEXT DEFAULT 'default')""")
    conn.execute(f"""CREATE TABLE IF NOT EXISTS {MSG_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT, role TEXT,
        content TEXT, tools_used TEXT DEFAULT '[]', citations TEXT DEFAULT '[]',
        sources_used TEXT DEFAULT '[]', multi_agent INTEGER DEFAULT 0,
        agents_used TEXT DEFAULT '[]', timestamp TEXT,
        FOREIGN KEY (conversation_id) REFERENCES {TABLE}(conversation_id))""")
    conn.commit()
    return conn

def create_conversation(title=None, user_id="default"):
    conv_id = str(uuid.uuid4())[:12]
    now = datetime.now().isoformat()
    if not title:
        title = f"Chat {datetime.now().strftime('%b %d, %H:%M')}"
    conn = _get_conn()
    conn.execute(f"INSERT INTO {TABLE} (conversation_id,title,created_at,updated_at,message_count,user_id) VALUES (?,?,?,?,0,?)",
        (conv_id, title, now, now, user_id))
    conn.commit(); conn.close()
    return conv_id

def save_message(conversation_id, role, content, tools_used=None, citations=None,
                 sources_used=None, multi_agent=False, agents_used=None, timestamp=None):
    if timestamp is None:
        timestamp = datetime.now().strftime("%H:%M")
    conn = _get_conn()
    conn.execute(f"INSERT INTO {MSG_TABLE} (conversation_id,role,content,tools_used,citations,sources_used,multi_agent,agents_used,timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
        (conversation_id, role, content, json.dumps(tools_used or []), json.dumps(citations or []),
         json.dumps(sources_used or []), int(multi_agent), json.dumps(agents_used or []), timestamp))
    conn.execute(f"UPDATE {TABLE} SET updated_at=?, message_count=message_count+1 WHERE conversation_id=?",
        (datetime.now().isoformat(), conversation_id))
    conn.commit(); conn.close()

def save_full_conversation(conversation_id, messages):
    conn = _get_conn()
    conn.execute(f"DELETE FROM {MSG_TABLE} WHERE conversation_id=?", (conversation_id,))
    for msg in messages:
        conn.execute(f"INSERT INTO {MSG_TABLE} (conversation_id,role,content,tools_used,citations,sources_used,multi_agent,agents_used,timestamp) VALUES (?,?,?,?,?,?,?,?,?)",
            (conversation_id, msg.get("role","user"), msg.get("content",""),
             json.dumps(msg.get("tools_used",[])), json.dumps(msg.get("citations",[])),
             json.dumps(msg.get("sources_used",[])), int(msg.get("multi_agent",False)),
             json.dumps(msg.get("agents_used",[])), msg.get("timestamp","")))
    conn.execute(f"UPDATE {TABLE} SET updated_at=?, message_count=? WHERE conversation_id=?",
        (datetime.now().isoformat(), len(messages), conversation_id))
    conn.commit(); conn.close()

def load_messages(conversation_id):
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {MSG_TABLE} WHERE conversation_id=? ORDER BY id ASC", (conversation_id,)).fetchall()
    conn.close()
    return [{"role":r["role"],"content":r["content"],"tools_used":json.loads(r["tools_used"]),
             "citations":json.loads(r["citations"]),"sources_used":json.loads(r["sources_used"]),
             "multi_agent":bool(r["multi_agent"]),"agents_used":json.loads(r["agents_used"]),
             "timestamp":r["timestamp"]} for r in rows]

def list_conversations(user_id="default", limit=20):
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    rows = conn.execute(f"SELECT * FROM {TABLE} WHERE user_id=? ORDER BY updated_at DESC LIMIT ?", (user_id, limit)).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_title(conversation_id, title):
    conn = _get_conn()
    conn.execute(f"UPDATE {TABLE} SET title=? WHERE conversation_id=?", (title, conversation_id))
    conn.commit(); conn.close()

def auto_title(conversation_id, first_message):
    title = first_message[:60].strip()
    if len(first_message) > 60: title += "..."
    update_title(conversation_id, title)
    return title

def delete_conversation(conversation_id):
    conn = _get_conn()
    conn.execute(f"DELETE FROM {MSG_TABLE} WHERE conversation_id=?", (conversation_id,))
    conn.execute(f"DELETE FROM {TABLE} WHERE conversation_id=?", (conversation_id,))
    conn.commit(); conn.close()

def get_conversation_info(conversation_id):
    conn = _get_conn(); conn.row_factory = sqlite3.Row
    row = conn.execute(f"SELECT * FROM {TABLE} WHERE conversation_id=?", (conversation_id,)).fetchone()
    conn.close()
    return dict(row) if row else None
