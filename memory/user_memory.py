"""
Agent Memory & Personalization System.
Persistent long-term memory per user with:
  - User profiles that grow smarter over time
  - Preference tracking ("You always ask about South region first")
  - Decision memory ("Last week you approved the budget cut scenario")
  - Pattern recognition across sessions
  - Personalized responses based on user history
"""
from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from loguru import logger

from config.settings import DB_PATH

# ── Tables ────────────────────────────────────────────────────────────────────
USER_PROFILE_TABLE = "nexus_user_profiles"
USER_MEMORY_TABLE = "nexus_user_memory"
USER_SESSION_TABLE = "nexus_user_sessions"
USER_PATTERN_TABLE = "nexus_user_patterns"


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")

    # Create tables
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {USER_PROFILE_TABLE} (
        user_id TEXT PRIMARY KEY DEFAULT 'default',
        display_name TEXT,
        created_at TEXT,
        last_active TEXT,
        total_interactions INTEGER DEFAULT 0,
        favorite_topics TEXT DEFAULT '[]',
        preferred_regions TEXT DEFAULT '[]',
        communication_style TEXT DEFAULT 'professional',
        timezone TEXT DEFAULT 'UTC',
        metadata TEXT DEFAULT '{{}}'
    )""")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {USER_MEMORY_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default',
        memory_type TEXT NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        importance REAL DEFAULT 0.5,
        access_count INTEGER DEFAULT 0,
        last_accessed TEXT,
        created_at TEXT,
        FOREIGN KEY (user_id) REFERENCES {USER_PROFILE_TABLE}(user_id)
    )""")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {USER_SESSION_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default',
        session_id TEXT NOT NULL,
        started_at TEXT,
        ended_at TEXT,
        query_count INTEGER DEFAULT 0,
        topics_discussed TEXT DEFAULT '[]',
        tools_used TEXT DEFAULT '[]',
        FOREIGN KEY (user_id) REFERENCES {USER_PROFILE_TABLE}(user_id)
    )""")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {USER_PATTERN_TABLE} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT DEFAULT 'default',
        pattern_type TEXT NOT NULL,
        pattern_key TEXT NOT NULL,
        pattern_value TEXT NOT NULL,
        frequency INTEGER DEFAULT 1,
        last_observed TEXT,
        FOREIGN KEY (user_id) REFERENCES {USER_PROFILE_TABLE}(user_id)
    )""")

    # Ensure default user exists
    conn.execute(f"""
    INSERT OR IGNORE INTO {USER_PROFILE_TABLE}
    (user_id, created_at, last_active)
    VALUES ('default', ?, ?)
    """, (datetime.now().isoformat(), datetime.now().isoformat()))

    conn.commit()
    return conn


# ── User Profile Management ───────────────────────────────────────────────────
def get_user_profile(user_id: str = "default") -> Dict[str, Any]:
    """Get or create a user profile."""
    try:
        conn = _get_conn()
        row = conn.execute(
            f"SELECT * FROM {USER_PROFILE_TABLE} WHERE user_id=?", (user_id,)
        ).fetchone()
        if row:
            result = dict(row)
            # Parse JSON fields
            for field in ("favorite_topics", "preferred_regions", "metadata"):
                try:
                    result[field] = json.loads(result[field])
                except (json.JSONDecodeError, TypeError):
                    result[field] = [] if field != "metadata" else {}
            conn.close()
            return result
        conn.close()
        return {"user_id": user_id, "total_interactions": 0}
    except Exception as e:
        logger.error(f"[UserMemory] get_user_profile failed: {e}")
        return {"user_id": user_id, "total_interactions": 0}


def update_user_profile(user_id: str = "default", **kwargs) -> bool:
    """Update fields in the user profile."""
    try:
        conn = _get_conn()
        # Serialize list/dict fields
        for key, val in kwargs.items():
            if isinstance(val, (list, dict)):
                kwargs[key] = json.dumps(val)

        sets = ", ".join(f"{k}=?" for k in kwargs.keys())
        values = list(kwargs.values()) + [user_id]
        conn.execute(
            f"UPDATE {USER_PROFILE_TABLE} SET {sets} WHERE user_id=?", values
        )
        conn.commit()
        conn.close()
        logger.debug(f"[UserMemory] Profile updated for {user_id}: {list(kwargs.keys())}")
        return True
    except Exception as e:
        logger.error(f"[UserMemory] update_user_profile failed: {e}")
        return False


def increment_interaction_count(user_id: str = "default") -> None:
    """Bump the interaction counter and last_active timestamp."""
    try:
        conn = _get_conn()
        conn.execute(
            f"UPDATE {USER_PROFILE_TABLE} SET total_interactions = total_interactions + 1, last_active = ? WHERE user_id=?",
            (datetime.now().isoformat(), user_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[UserMemory] increment_interaction_count failed: {e}")


# ── Memory Storage (granular facts) ──────────────────────────────────────────
def store_memory(user_id: str, memory_type: str, key: str, value: str,
                  importance: float = 0.5) -> bool:
    """
    Store a memory fact.
    memory_type: 'preference' | 'decision' | 'insight' | 'entity' | 'pattern'
    """
    valid_types = {"preference", "decision", "insight", "entity", "pattern"}
    if memory_type not in valid_types:
        memory_type = "insight"

    try:
        conn = _get_conn()
        now = datetime.now().isoformat()
        conn.execute(f"""
        INSERT INTO {USER_MEMORY_TABLE}
        (user_id, memory_type, key, value, importance, created_at, last_accessed)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (user_id, memory_type, key, value, importance, now, now))
        conn.commit()
        conn.close()
        logger.debug(f"[UserMemory] Stored [{memory_type}] {key} for {user_id}")
        return True
    except sqlite3.IntegrityError:
        # Update existing
        try:
            conn = _get_conn()
            conn.execute(f"""
            UPDATE {USER_MEMORY_TABLE}
            SET value=?, importance=?, last_accessed=?
            WHERE user_id=? AND key=?
            """, (value, importance, datetime.now().isoformat(), user_id, key))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            logger.error(f"[UserMemory] store_memory update failed: {e}")
            return False
    except Exception as e:
        logger.error(f"[UserMemory] store_memory failed: {e}")
        return False


def recall_memories(user_id: str, memory_type: str = None,
                     query: str = None, limit: int = 5) -> List[Dict[str, Any]]:
    """Recall memories with optional type filter and keyword search."""
    try:
        conn = _get_conn()
        sql = f"SELECT * FROM {USER_MEMORY_TABLE} WHERE user_id=?"
        params = [user_id]

        if memory_type:
            sql += " AND memory_type=?"
            params.append(memory_type)

        if query:
            keywords = query.lower().split()
            conditions = " AND ".join(
                "(LOWER(key) LIKE ? OR LOWER(value) LIKE ?)" for _ in keywords
            )
            sql += f" AND ({conditions})"
            for kw in keywords:
                params += [f"%{kw}%", f"%{kw}%"]

        sql += " ORDER BY importance DESC, access_count DESC, last_accessed DESC LIMIT ?"
        params.append(limit)

        rows = conn.execute(sql, params).fetchall()
        results = [dict(row) for row in rows]

        # Bump access count
        for row in rows:
            conn.execute(f"""
            UPDATE {USER_MEMORY_TABLE}
            SET access_count = access_count + 1, last_accessed = ?
            WHERE id = ?
            """, (datetime.now().isoformat(), row["id"]))
        conn.commit()
        conn.close()
        return results
    except Exception as e:
        logger.error(f"[UserMemory] recall_memories failed: {e}")
        return []


def forget_memory(user_id: str, key: str) -> bool:
    """Delete a memory by key."""
    try:
        conn = _get_conn()
        conn.execute(
            f"DELETE FROM {USER_MEMORY_TABLE} WHERE user_id=? AND key=?", (user_id, key)
        )
        conn.commit()
        conn.close()
        logger.info(f"[UserMemory] Forgot memory: {key} for {user_id}")
        return True
    except Exception as e:
        logger.error(f"[UserMemory] forget_memory failed: {e}")
        return False


# ── Session Tracking ──────────────────────────────────────────────────────────
def start_session(user_id: str = "default", session_id: str = None) -> str:
    """Start a new user session."""
    if not session_id:
        session_id = f"session_{int(time.time())}"
    try:
        conn = _get_conn()
        conn.execute(f"""
        INSERT INTO {USER_SESSION_TABLE}
        (user_id, session_id, started_at, query_count)
        VALUES (?, ?, ?, 0)
        """, (user_id, session_id, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logger.debug(f"[UserMemory] Session started: {session_id} for {user_id}")
    except Exception as e:
        logger.error(f"[UserMemory] start_session failed: {e}")
    return session_id


def end_session(session_id: str) -> None:
    """End a user session."""
    try:
        conn = _get_conn()
        conn.execute(
            f"UPDATE {USER_SESSION_TABLE} SET ended_at = ? WHERE session_id = ?",
            (datetime.now().isoformat(), session_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[UserMemory] end_session failed: {e}")


def log_session_query(session_id: str, topic: str, tools: List[str]) -> None:
    """Log a query in the current session for topic tracking."""
    try:
        conn = _get_conn()
        # Update query count
        conn.execute(
            f"UPDATE {USER_SESSION_TABLE} SET query_count = query_count + 1 WHERE session_id=?",
            (session_id,)
        )

        # Append topic
        row = conn.execute(
            "SELECT topics_discussed FROM nexus_user_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row:
            try:
                topics = json.loads(row["topics_discussed"])
            except (json.JSONDecodeError, TypeError):
                topics = []
            topics.append(topic)
            conn.execute(
                "UPDATE nexus_user_sessions SET topics_discussed=? WHERE session_id=?",
                (json.dumps(topics), session_id)
            )

        # Append tools
        row = conn.execute(
            "SELECT tools_used FROM nexus_user_sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if row:
            try:
                used = json.loads(row["tools_used"])
            except (json.JSONDecodeError, TypeError):
                used = []
            for t in tools:
                if t not in used:
                    used.append(t)
            conn.execute(
                "UPDATE nexus_user_sessions SET tools_used=? WHERE session_id=?",
                (json.dumps(used), session_id)
            )

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[UserMemory] log_session_query failed: {e}")


# ── Pattern Detection ────────────────────────────────────────────────────────
def track_pattern(user_id: str, pattern_type: str, key: str, value: str) -> None:
    """Track a behavioral pattern (e.g., frequent topic, common tool)."""
    try:
        conn = _get_conn()
        existing = conn.execute(
            f"SELECT * FROM {USER_PATTERN_TABLE} WHERE user_id=? AND pattern_type=? AND pattern_key=?",
            (user_id, pattern_type, key)
        ).fetchone()

        if existing:
            conn.execute(f"""
            UPDATE {USER_PATTERN_TABLE}
            SET frequency = frequency + 1, pattern_value = ?, last_observed = ?
            WHERE user_id=? AND pattern_type=? AND pattern_key=?
            """, (value, datetime.now().isoformat(), user_id, pattern_type, key))
        else:
            conn.execute(f"""
            INSERT INTO {USER_PATTERN_TABLE}
            (user_id, pattern_type, pattern_key, pattern_value, frequency, last_observed)
            VALUES (?, ?, ?, ?, 1, ?)
            """, (user_id, pattern_type, key, value, datetime.now().isoformat()))

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"[UserMemory] track_pattern failed: {e}")


def get_user_patterns(user_id: str, pattern_type: str = None) -> List[Dict[str, Any]]:
    """Get detected patterns for a user, sorted by frequency."""
    try:
        conn = _get_conn()
        sql = f"SELECT * FROM {USER_PATTERN_TABLE} WHERE user_id=?"
        params = [user_id]
        if pattern_type:
            sql += " AND pattern_type=?"
            params.append(pattern_type)
        sql += " ORDER BY frequency DESC"
        rows = conn.execute(sql, params).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"[UserMemory] get_user_patterns failed: {e}")
        return []


# ── Automatic Profile Learning ────────────────────────────────────────────────
def learn_from_interaction(user_id: str, query: str, result: Dict[str, Any]) -> None:
    """
    Automatically learn from an interaction.
    Call this after every query to gradually build the user profile.
    """
    try:
        from config.llm_config import get_llm

        profile = get_user_profile(user_id)
        tools = result.get("tools_used", [])
        topics = _extract_topics_from_result(result)

        # Track topics pattern
        for topic in topics:
            track_pattern(user_id, "topic", topic.lower(), topic)

        # Track tool usage pattern
        for tool in tools:
            track_pattern(user_id, "tool", tool, tool)

        # Extract regions mentioned
        regions = _extract_regions(query)
        if regions:
            for region in regions:
                track_pattern(user_id, "region", region.lower(), region)

        # Every 10 interactions, do deep learning
        interaction_count = profile.get("total_interactions", 0) + 1
        if interaction_count % 10 == 0:
            _deep_learn_user(user_id, llm=get_llm())

        # Update profile with aggregated data
        _update_profile_from_patterns(user_id)

        # Increment counter
        increment_interaction_count(user_id)

    except Exception as e:
        logger.error(f"[UserMemory] learn_from_interaction failed: {e}")


def _extract_topics_from_result(result: Dict[str, Any]) -> List[str]:
    """Extract key topics from a query result."""
    topics = []
    answer = result.get("final_answer", "")
    query = result.get("query", "")

    # Simple keyword-based topic extraction
    topic_keywords = {
        "revenue": ["revenue", "sales", "income"],
        "region": ["region", "north", "south", "east", "west"],
        "product": ["product", "item", "sku"],
        "customer": ["customer", "client", "user"],
        "cost": ["cost", "expense", "spend", "budget"],
        "performance": ["performance", "metric", "kpi"],
        "report": ["report", "summary", "analysis"],
        "policy": ["policy", "rule", "procedure"],
    }

    text = f"{query} {answer}".lower()
    for topic, keywords in topic_keywords.items():
        if any(kw in text for kw in keywords):
            topics.append(topic)

    return topics[:3]  # Max 3 topics per interaction


def _extract_regions(text: str) -> List[str]:
    """Extract region mentions from text."""
    regions = []
    lower = text.lower()
    for region in ("north", "south", "east", "west", "central", "northeast", "northwest",
                    "southeast", "southwest"):
        if region in lower:
            regions.append(region.capitalize())
    return regions


def _deep_learn_user(user_id: str, llm=None) -> None:
    """Use LLM to deeply analyze user behavior and extract insights."""
    if llm is None:
        try:
            from config.llm_config import get_llm
            llm = get_llm()
        except Exception:
            return

    try:
        # Get recent memories
        recent = recall_memories(user_id, limit=20)
        patterns = get_user_patterns(user_id)
        profile = get_user_profile(user_id)

        context = f"""User Profile:
- Total interactions: {profile.get('total_interactions', 0)}
- Last active: {profile.get('last_active', 'never')}
- Communication style: {profile.get('communication_style', 'professional')}

Recent memories ({len(recent)}):
"""
        for m in recent[:10]:
            context += f"- [{m['memory_type']}] {m['key']}: {m['value'][:100]}\n"

        context += f"\nPatterns detected ({len(patterns)}):\n"
        for p in patterns[:10]:
            context += f"- {p['pattern_type']}: {p['pattern_key']} (frequency: {p['frequency']})\n"

        prompt = f"""Analyze this user's behavior and extract key insights.

{context}

Output insights (max 5):
KEY: <short_key> | VALUE: <insight> | TYPE: <preference|insight|entity|decision>

Focus on preferences, habits, frequently asked topics, and behavioral patterns."""

        response = llm.invoke(prompt)
        for line in response.strip().split("\n"):
            if "KEY:" in line and "VALUE:" in line:
                try:
                    parts = {}
                    for p in line.split("|"):
                        if ":" in p:
                            k = p.split(":")[0].strip()
                            v = p.split(":", 1)[1].strip()
                            parts[k] = v
                    key = parts.get("KEY", "")
                    value = parts.get("VALUE", "")
                    mem_type = parts.get("TYPE", "insight").lower()
                    if key and value:
                        store_memory(user_id, mem_type, key, value, importance=0.7)
                except Exception:
                    pass
        logger.info(f"[UserMemory] Deep learning complete for {user_id}")

    except Exception as e:
        logger.error(f"[UserMemory] _deep_learn_user failed: {e}")


def _update_profile_from_patterns(user_id: str) -> None:
    """Aggregate pattern data into the user profile for quick access."""
    try:
        topics = get_user_patterns(user_id, "topic")
        regions = get_user_patterns(user_id, "region")

        if topics:
            sorted_topics = sorted(topics, key=lambda x: x["frequency"], reverse=True)
            fav_topics = [t["pattern_value"] for t in sorted_topics[:5]]
            update_user_profile(user_id, favorite_topics=fav_topics)

        if regions:
            sorted_regions = sorted(regions, key=lambda x: x["frequency"], reverse=True)
            pref_regions = [r["pattern_value"] for r in sorted_regions[:5]]
            update_user_profile(user_id, preferred_regions=pref_regions)

    except Exception as e:
        logger.error(f"[UserMemory] _update_profile_from_patterns failed: {e}")


# ── Personalized Context Builder ─────────────────────────────────────────────
def build_personalized_context(user_id: str, query: str) -> str:
    """
    Build a rich personalized context string for LLM prompt injection.
    Includes: relevant memories, user preferences, detected patterns.
    """
    profile = get_user_profile(user_id)
    parts = []

    # User profile summary
    if profile.get("total_interactions", 0) > 0:
        profile_info = "[User Profile] You are assisting a returning user."
        if profile.get("favorite_topics"):
            topics = profile["favorite_topics"]
            if isinstance(topics, list) and topics:
                profile_info += f" They frequently ask about: {', '.join(topics[:3])}."
        if profile.get("preferred_regions"):
            regions = profile["preferred_regions"]
            if isinstance(regions, list) and regions:
                profile_info += f" They often focus on the {', '.join(regions[:2])} region(s)."
        parts.append(profile_info)

    # Relevant memories
    memories = recall_memories(user_id, query=query, limit=3)
    if memories:
        mem_lines = ["[Personalized Memory]"]
        for m in memories:
            mem_lines.append(f"- {m['key']}: {m['value']}")
        parts.append("\n".join(mem_lines))

    # Recent decisions
    decisions = recall_memories(user_id, memory_type="decision", limit=2)
    if decisions:
        dec_lines = ["[Past Decisions]"]
        for d in decisions:
            dec_lines.append(f"- {d['key']}: {d['value']}")
        parts.append("\n".join(dec_lines))

    # Patterns
    patterns = get_user_patterns(user_id)
    if patterns:
        pattern_lines = ["[User Patterns]"]
        for p in patterns[:3]:
            pattern_lines.append(
                f"- {p['pattern_type']}: '{p['pattern_key']}' "
                f"(observed {p['frequency']} times)"
            )
        parts.append("\n".join(pattern_lines))

    return "\n".join(parts) if parts else ""


# ── Convenience API ──────────────────────────────────────────────────────────
def remember_decision(user_id: str, decision_key: str, decision_value: str) -> None:
    """Record a user decision for future reference."""
    store_memory(user_id, "decision", decision_key, decision_value, importance=0.9)
    logger.info(f"[UserMemory] Decision recorded: {decision_key}")


def remember_preference(user_id: str, pref_key: str, pref_value: str) -> None:
    """Record a user preference."""
    store_memory(user_id, "preference", pref_key, pref_value, importance=0.7)
    logger.info(f"[UserMemory] Preference recorded: {pref_key}")


def get_user_summary(user_id: str = "default") -> Dict[str, Any]:
    """Get a comprehensive summary of a user's profile and activity."""
    profile = get_user_profile(user_id)
    memories = recall_memories(user_id, limit=10)
    patterns = get_user_patterns(user_id)
    sessions = _get_recent_sessions(user_id, n=5)

    return {
        "profile": profile,
        "total_memories": len(memories),
        "recent_memories": memories,
        "total_patterns": len(patterns),
        "top_patterns": patterns[:5],
        "recent_sessions": sessions,
    }


def _get_recent_sessions(user_id: str, n: int = 5) -> List[Dict[str, Any]]:
    """Get recent sessions for a user."""
    try:
        conn = _get_conn()
        rows = conn.execute(
            f"SELECT * FROM {USER_SESSION_TABLE} WHERE user_id=? ORDER BY started_at DESC LIMIT ?",
            (user_id, n)
        ).fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"[UserMemory] _get_recent_sessions failed: {e}")
        return []
