"""
Agent personas — names and identities for the 6 autonomous agents.

Each agent has:
  - `key`         — internal identifier (matches scheduler job id / module)
  - `default_name`— the character name shipped with the product
  - `role_tag`    — short human-readable role shown next to the name
  - `description` — one-sentence "what this person does" copy
  - `emoji`       — optional visual identifier

Names are customizable per business. Overrides live in `nexus_agent_personas`,
which has one row per (business_id, agent_key) pair. Absence of a row means
"use the default name".

The whole thing is thin on purpose — this module is about *identity*, not
behavior. Actual agent work lives in `agents/briefing.py`,
`agents/background/invoice_reminder.py`, etc.
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from config.settings import DB_PATH

TABLE = "nexus_agent_personas"


# ── Defaults — the cast ─────────────────────────────────────────────────────
DEFAULTS: Dict[str, Dict[str, str]] = {
    "morning_briefing": {
        "default_name": "Atlas",
        "role_tag":     "Chief of staff",
        "description":  "Writes your one-page morning briefing every day at 08:00.",
        "emoji":        "☀️",
    },
    "invoice_reminder": {
        "default_name": "Kira",
        "role_tag":     "Invoice chaser",
        "description":  "Spots overdue invoices and drafts polite reminder emails for your approval.",
        "emoji":        "💰",
    },
    "stale_deal_watcher": {
        "default_name": "Arjun",
        "role_tag":     "Pipeline watcher",
        "description":  "Flags deals that haven't moved in 2+ weeks and suggests a next action.",
        "emoji":        "🎯",
    },
    "meeting_prep": {
        "default_name": "Sage",
        "role_tag":     "Meeting prep",
        "description":  "30 minutes before a meeting, prepares a briefing on the contact and open deals.",
        "emoji":        "📎",
    },
    "email_triage": {
        "default_name": "Iris",
        "role_tag":     "Inbox triage",
        "description":  "Reads new emails every 15 minutes, classifies them, and queues reply drafts.",
        "emoji":        "📬",
    },
    "memory_consolidate": {
        "default_name": "Echo",
        "role_tag":     "Memory keeper",
        "description":  "Weekly: reviews conversation history and distils what's worth remembering.",
        "emoji":        "🧠",
    },
}

# Scheduler job-id ↔ agent-key mapping (for activity summary lookup)
SCHEDULER_JOB_IDS: Dict[str, str] = {
    "morning_briefing":    "agent-morning-briefing",
    "invoice_reminder":    "agent-invoice-reminder",
    "stale_deal_watcher":  "agent-stale-deal-watcher",
    "meeting_prep":        "agent-meeting-prep",
    "email_triage":        "agent-email-triage",
    "memory_consolidate":  "agent-memory-consolidate",
}


# ── Storage ─────────────────────────────────────────────────────────────────
def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            business_id TEXT NOT NULL,
            agent_key   TEXT NOT NULL,
            custom_name TEXT NOT NULL,
            enabled     INTEGER NOT NULL DEFAULT 1,
            updated_at  TEXT NOT NULL,
            PRIMARY KEY (business_id, agent_key)
        )
    """)
    conn.commit()
    return conn


def _valid_name(s: str) -> str:
    s = (s or "").strip()
    if not s:
        raise ValueError("Name cannot be empty")
    if len(s) > 40:
        raise ValueError("Name is too long (max 40 chars)")
    return s


# ── Public API ──────────────────────────────────────────────────────────────
def _base(agent_key: str) -> Dict[str, str]:
    if agent_key not in DEFAULTS:
        raise KeyError(f"Unknown agent key: {agent_key}")
    return DEFAULTS[agent_key]


def get_persona(business_id: str, agent_key: str) -> Dict:
    """Resolved persona (custom name if set, else default)."""
    base = _base(agent_key)
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT custom_name, enabled FROM {TABLE} "
            f"WHERE business_id = ? AND agent_key = ?",
            (business_id, agent_key),
        ).fetchone()
    finally:
        conn.close()
    name = row["custom_name"] if row and row["custom_name"] else base["default_name"]
    return {
        "agent_key":    agent_key,
        "name":         name,
        "default_name": base["default_name"],
        "role_tag":     base["role_tag"],
        "description":  base["description"],
        "emoji":        base["emoji"],
        "is_custom":    bool(row and row["custom_name"]),
        "enabled":      bool(row["enabled"]) if row else True,
    }


def list_personas(business_id: str) -> List[Dict]:
    """All 6 personas, in a stable presentation order."""
    order = [
        "morning_briefing",     # start of day
        "email_triage",         # throughout the day
        "invoice_reminder",     # financial follow-through
        "stale_deal_watcher",   # pipeline health
        "meeting_prep",         # just-in-time
        "memory_consolidate",   # weekly reflection
    ]
    # Attach scheduler next-run times where available
    next_runs: Dict[str, str] = {}
    try:
        from agents.background.scheduler import list_jobs
        for j in list_jobs():
            next_runs[j["id"]] = j.get("next_run") or ""
    except Exception:
        pass

    out = []
    for key in order:
        p = get_persona(business_id, key)
        job_id = SCHEDULER_JOB_IDS.get(key)
        p["next_run"] = next_runs.get(job_id, "") if job_id else ""
        p["last_activity"] = _last_activity(business_id, key)
        out.append(p)
    return out


def set_name(business_id: str, agent_key: str, name: str) -> Dict:
    """Rename an agent. Pass empty string to reset to default."""
    _base(agent_key)  # validate key exists
    name = name.strip()
    conn = _get_conn()
    try:
        if not name:
            conn.execute(
                f"DELETE FROM {TABLE} WHERE business_id = ? AND agent_key = ?",
                (business_id, agent_key),
            )
        else:
            name = _valid_name(name)
            conn.execute(
                f"INSERT INTO {TABLE} (business_id, agent_key, custom_name, enabled, updated_at) "
                f"VALUES (?, ?, ?, 1, ?) "
                f"ON CONFLICT(business_id, agent_key) DO UPDATE SET "
                f"custom_name = excluded.custom_name, updated_at = excluded.updated_at",
                (business_id, agent_key, name, datetime.utcnow().isoformat()),
            )
        conn.commit()
    finally:
        conn.close()
    return get_persona(business_id, agent_key)


def set_enabled(business_id: str, agent_key: str, enabled: bool) -> Dict:
    """Toggle whether this agent runs for this business."""
    _base(agent_key)
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {TABLE} (business_id, agent_key, custom_name, enabled, updated_at) "
            f"VALUES (?, ?, '', ?, ?) "
            f"ON CONFLICT(business_id, agent_key) DO UPDATE SET "
            f"enabled = excluded.enabled, updated_at = excluded.updated_at",
            (business_id, agent_key, 1 if enabled else 0, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()
    return get_persona(business_id, agent_key)


# ── Activity summary ────────────────────────────────────────────────────────
def _last_activity(business_id: str, agent_key: str) -> Dict:
    """
    Return {last_ran, last_24h_count, surface} — where the agent's output
    lives so the UI can link to it.
    """
    info: Dict = {"last_ran": None, "last_24h_count": 0, "surface": None}
    try:
        conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row
        try:
            if agent_key == "morning_briefing":
                row = conn.execute(
                    "SELECT created_at FROM nexus_briefings "
                    "WHERE business_id = ? ORDER BY created_at DESC LIMIT 1",
                    (business_id,),
                ).fetchone()
                if row: info["last_ran"] = row["created_at"]
                cnt = conn.execute(
                    "SELECT COUNT(*) AS n FROM nexus_briefings "
                    "WHERE business_id = ? AND created_at > datetime('now','-1 day')",
                    (business_id,),
                ).fetchone()
                info["last_24h_count"] = int(cnt["n"] or 0) if cnt else 0
                info["surface"] = "/"  # Dashboard
            elif agent_key == "invoice_reminder":
                row = conn.execute(
                    "SELECT created_at FROM nexus_approvals "
                    "WHERE business_id = ? AND tool_name = 'send_invoice_email' "
                    "ORDER BY created_at DESC LIMIT 1",
                    (business_id,),
                ).fetchone()
                if row: info["last_ran"] = row["created_at"]
                cnt = conn.execute(
                    "SELECT COUNT(*) AS n FROM nexus_approvals "
                    "WHERE business_id = ? AND tool_name = 'send_invoice_email' "
                    "AND created_at > datetime('now','-1 day')",
                    (business_id,),
                ).fetchone()
                info["last_24h_count"] = int(cnt["n"] or 0) if cnt else 0
                info["surface"] = "/approvals"
            elif agent_key == "email_triage":
                row = conn.execute(
                    "SELECT processed_at FROM nexus_email_messages "
                    "WHERE business_id = ? ORDER BY processed_at DESC LIMIT 1",
                    (business_id,),
                ).fetchone()
                if row: info["last_ran"] = row["processed_at"]
                cnt = conn.execute(
                    "SELECT COUNT(*) AS n FROM nexus_email_messages "
                    "WHERE business_id = ? AND processed_at > datetime('now','-1 day')",
                    (business_id,),
                ).fetchone()
                info["last_24h_count"] = int(cnt["n"] or 0) if cnt else 0
                info["surface"] = "/approvals"
            # Other agents (stale_deal_watcher / meeting_prep / memory_consolidate)
            # land in notifications — leave info.last_ran null for now rather than
            # inventing a wrong number.
        finally:
            conn.close()
    except Exception as e:
        logger.debug(f"[Personas] activity lookup for {agent_key} failed: {e}")
    return info
