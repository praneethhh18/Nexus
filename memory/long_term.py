"""
Long-Term Memory — persists facts across sessions in SQLite.
Auto-extracts key facts from conversations after every 5 turns.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger

from config.settings import DB_PATH

LT_TABLE = "nexus_long_term_memory"
CATEGORIES = {"preference", "insight", "entity", "decision"}


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {LT_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        key TEXT UNIQUE NOT NULL,
        value TEXT NOT NULL,
        category TEXT DEFAULT 'insight',
        created_at TEXT,
        updated_at TEXT
    )""")
    conn.commit()
    return conn


def store_fact(key: str, value: str, category: str = "insight") -> bool:
    """Store or update a persistent fact."""
    if category not in CATEGORIES:
        category = "insight"
    now = datetime.now().isoformat()
    try:
        conn = _get_conn()
        conn.execute(f"""
        INSERT INTO {LT_TABLE} (key, value, category, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(key) DO UPDATE SET
            value=excluded.value,
            category=excluded.category,
            updated_at=excluded.updated_at
        """, (key, value, category, now, now))
        conn.commit()
        conn.close()
        logger.debug(f"[LTM] Stored: [{category}] {key} = {value[:60]}")
        return True
    except Exception as e:
        logger.error(f"[LTM] store_fact failed: {e}")
        return False


def recall(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Search facts using keyword matching in key+value fields."""
    try:
        conn = _get_conn()
        keywords = query.lower().split()
        # Build a LIKE clause for each keyword
        conditions = " OR ".join(
            "(LOWER(key) LIKE ? OR LOWER(value) LIKE ?)" for _ in keywords
        )
        params = []
        for kw in keywords:
            params += [f"%{kw}%", f"%{kw}%"]
        rows = conn.execute(
            f"SELECT * FROM {LT_TABLE} WHERE {conditions} LIMIT ?",
            params + [limit]
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"[LTM] recall failed: {e}")
        return []


def get_recent_facts(n: int = 10) -> List[Dict[str, Any]]:
    """Return n most recently updated facts."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            f"SELECT * FROM {LT_TABLE} ORDER BY updated_at DESC LIMIT ?", (n,)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"[LTM] get_recent_facts failed: {e}")
        return []


def forget(key: str) -> bool:
    """Delete a fact by key."""
    try:
        conn = _get_conn()
        conn.execute(f"DELETE FROM {LT_TABLE} WHERE key=?", (key,))
        conn.commit()
        conn.close()
        logger.info(f"[LTM] Forgot: {key}")
        return True
    except Exception as e:
        logger.error(f"[LTM] forget failed: {e}")
        return False


def auto_extract_facts(conversation_history: str) -> int:
    """
    Ask LLM to extract key facts from a conversation and store them.
    Returns number of facts stored.
    """
    try:
        from config.llm_config import get_llm
        llm = get_llm()
        prompt = f"""Extract key facts, preferences, decisions, or entities from this conversation.
For each fact output one line:
KEY: <short_key> | VALUE: <fact_value> | CATEGORY: <preference|insight|entity|decision>

Only extract concrete, reusable facts (not conversational filler).
Maximum 5 facts.

CONVERSATION:
{conversation_history[-3000:]}

FACTS:"""

        response = llm.invoke(prompt)
        stored = 0
        for line in response.strip().split("\n"):
            if "KEY:" in line and "VALUE:" in line:
                try:
                    parts = {p.split(":")[0].strip(): p.split(":", 1)[1].strip()
                             for p in line.split("|") if ":" in p}
                    key = parts.get("KEY", "")
                    value = parts.get("VALUE", "")
                    category = parts.get("CATEGORY", "insight").lower()
                    if key and value:
                        store_fact(key, value, category)
                        stored += 1
                except Exception:
                    pass
        logger.info(f"[LTM] Auto-extracted {stored} facts from conversation.")
        return stored
    except Exception as e:
        logger.warning(f"[LTM] auto_extract_facts failed: {e}")
        return 0


def build_memory_context(query: str) -> str:
    """Recall relevant facts and format for LLM prompt injection."""
    facts = recall(query, limit=3)
    if not facts:
        return ""
    lines = [f"[Memory] {f['category'].upper()}: {f['key']} = {f['value']}" for f in facts]
    return "Relevant past context:\n" + "\n".join(lines)
