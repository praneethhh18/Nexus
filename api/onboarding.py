"""
Onboarding state — tracks progress through the 6-step setup flow so the UI
can (a) resume where the user left off on any device, and (b) keep showing a
checklist widget on the dashboard until every step is done.

State lives in `nexus_onboarding_state`, one row per (business_id, user_id).
Absence of a row means "not started" — safe default.

The 6 steps are driven by the product roadmap:

    profile       — business profile (name, industry, size, timezone, currency)
    agents        — chose which agents to enable
    data_source   — uploaded a CSV or connected email
    document      — uploaded a document to RAG
    first_run     — ran any agent manually at least once
    celebrated    — dismissed the "you're all set" screen

The table only stores booleans + a skipped flag. It never stores the values
the user entered in each step — that data already lives in the business /
documents / agent tables, which is the source of truth. This module is just
a progress tracker.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from typing import Dict, List

from loguru import logger

from config.db import get_conn, list_tables
from utils.timez import now_iso

TABLE = "nexus_onboarding_state"

# Declarative step definition — keeps the UI and backend in sync.
STEPS: List[Dict[str, str]] = [
    {
        "key": "profile",
        "title": "Business profile",
        "description": "Business name, type, industry, size, and first goal",
        "cta": "Save profile",
        "route": "/settings",
    },
    {
        "key": "agents",
        "title": "Industry workspace",
        "description": "Here's what we'll pre-configure for your industry. Confirm to apply, or go back to change your profile.",
        "cta": "Apply this setup",
        "route": "/agents",
    },
    {
        "key": "data_source",
        "title": "Bring in your contacts",
        "description": "Upload a CSV right here so your CRM starts with real leads instead of empty cards. Skip if you'd rather start blank.",
        "cta": "Import contacts",
        "route": "/database",
    },
    {
        "key": "document",
        "title": "Upload a company document",
        "description": "One policy, catalog, or FAQ is enough — the AI uses it as safe context for first answers.",
        "cta": "Upload document",
        "route": "/documents",
    },
    {
        "key": "first_run",
        "title": "Try an agent right now",
        "description": "Click an agent below to run a sample task. The result shows up inline — no leaving this page.",
        "cta": "Run an agent",
        "route": "/agents",
    },
    {
        "key": "celebrated",
        "title": "You're all set",
        "description": "Acknowledge the setup is done — unlocks the celebration state",
        "cta": "Finish",
        "route": "/",
    },
]
STEP_KEYS = [s["key"] for s in STEPS]


# ── Storage ─────────────────────────────────────────────────────────────────
def _conn():
    conn = get_conn()
    cols = ", ".join(f"step_{k} INTEGER NOT NULL DEFAULT 0" for k in STEP_KEYS)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            business_id   TEXT NOT NULL,
            user_id       TEXT NOT NULL,
            {cols},
            skipped       INTEGER NOT NULL DEFAULT 0,
            completed_at  TEXT,
            updated_at    TEXT NOT NULL,
            PRIMARY KEY (business_id, user_id)
        )
    """)
    conn.commit()
    return conn


def _row(business_id: str, user_id: str) -> Dict:
    """Return the raw row as a dict, creating it lazily if missing."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TABLE} WHERE business_id = ? AND user_id = ?",
            (business_id, user_id),
        ).fetchone()
        if row is None:
            now = now_iso()
            conn.execute(
                f"INSERT INTO {TABLE} (business_id, user_id, updated_at) VALUES (?, ?, ?)",
                (business_id, user_id, now),
            )
            conn.commit()
            row = conn.execute(
                f"SELECT * FROM {TABLE} WHERE business_id = ? AND user_id = ?",
                (business_id, user_id),
            ).fetchone()
    finally:
        conn.close()
    return dict(row)


def _write(business_id: str, user_id: str, updates: Dict) -> None:
    updates = {**updates, "updated_at": now_iso()}
    cols = ", ".join(f"{k} = ?" for k in updates.keys())
    values = list(updates.values()) + [business_id, user_id]
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET {cols} WHERE business_id = ? AND user_id = ?",
            values,
        )
        conn.commit()
    finally:
        conn.close()


# ── Auto-detection ─────────────────────────────────────────────────────────
# A step counts as "done" if the user has already accomplished its underlying
# task, even if they never clicked the wizard button. We check for real data.
def _autodetect(business_id: str) -> Dict[str, bool]:
    """Infer completion from the actual state of the workspace."""
    auto: Dict[str, bool] = {k: False for k in STEP_KEYS}
    try:
        conn = get_conn()
        conn.row_factory = sqlite3.Row
        try:
            # profile: business row exists with a non-empty name
            try:
                from api.businesses import BUSINESSES_TABLE
                row = conn.execute(
                    f"SELECT name, industry, description FROM {BUSINESSES_TABLE} WHERE id = ?",
                    (business_id,),
                ).fetchone()
                desc = row["description"] or "" if row else ""
                has_full_profile = (
                    "Business type:" in desc
                    and "Company size:" in desc
                    and "Primary goal:" in desc
                )
                if row and (row["name"] or "").strip() and (row["industry"] or "").strip() and has_full_profile:
                    auto["profile"] = True
            except Exception:
                pass

            # data_source: any imported rows beyond seed tables
            try:
                n = sum(1 for t in list_tables(conn) if t.startswith("imported_"))
                if n > 0:
                    auto["data_source"] = True
            except Exception:
                pass

            # document: any chunk in the RAG collection for this business
            # Chroma doesn't live in SQLite; instead count nexus_documents table.
            try:
                row = conn.execute(
                    "SELECT COUNT(*) AS n FROM nexus_documents WHERE business_id = ?",
                    (business_id,),
                ).fetchone()
                if row and int(row["n"] or 0) > 0:
                    auto["document"] = True
            except Exception:
                pass

            # first_run: at least one row in nexus_agent_runs for this business
            try:
                row = conn.execute(
                    "SELECT COUNT(*) AS n FROM nexus_agent_runs WHERE business_id = ?",
                    (business_id,),
                ).fetchone()
                if row and int(row["n"] or 0) > 0:
                    auto["first_run"] = True
            except Exception:
                pass

            # agents: anyone has paused, renamed, or otherwise touched a persona
            try:
                row = conn.execute(
                    "SELECT COUNT(*) AS n FROM nexus_agent_personas WHERE business_id = ?",
                    (business_id,),
                ).fetchone()
                if row and int(row["n"] or 0) > 0:
                    auto["agents"] = True
            except Exception:
                pass
        finally:
            conn.close()
    except Exception as e:
        logger.debug(f"[Onboarding] autodetect failed: {e}")
    return auto


# ── Public API ──────────────────────────────────────────────────────────────
def get_state(business_id: str, user_id: str) -> Dict:
    """
    Return the full onboarding state for one user in one business, with
    auto-detected completions merged in so skipping the wizard doesn't leave
    real progress invisible.
    """
    row = _row(business_id, user_id)
    auto = _autodetect(business_id)

    step_results: List[Dict] = []
    persisted_updates: Dict = {}
    for step in STEPS:
        key = step["key"]
        col = f"step_{key}"
        done = bool(row.get(col)) or auto.get(key, False)
        # If autodetect found it done, persist so we don't recompute forever.
        if not row.get(col) and auto.get(key, False):
            persisted_updates[col] = 1
        step_results.append({**step, "done": done})

    if persisted_updates:
        _write(business_id, user_id, persisted_updates)

    # A user is "complete" when every step is done. `celebrated` only flips
    # when they explicitly dismiss — otherwise the checklist stays visible.
    all_done = all(s["done"] for s in step_results)
    celebrated = bool(row.get("step_celebrated"))
    return {
        "steps": step_results,
        "skipped": bool(row.get("skipped")),
        "all_done": all_done,
        "celebrated": celebrated,
        "completed_at": row.get("completed_at"),
    }


def complete_step(business_id: str, user_id: str, step_key: str) -> Dict:
    if step_key not in STEP_KEYS:
        raise ValueError(f"Unknown onboarding step: {step_key}")
    updates = {f"step_{step_key}": 1}
    # If this is the last remaining step, stamp the completion time.
    state = get_state(business_id, user_id)
    remaining = [s for s in state["steps"] if not s["done"] and s["key"] != step_key]
    if not remaining:
        updates["completed_at"] = now_iso()
    _write(business_id, user_id, updates)
    return get_state(business_id, user_id)


def skip_all(business_id: str, user_id: str) -> Dict:
    """Dismiss the wizard entirely. The checklist widget also hides."""
    _row(business_id, user_id)  # ensure row exists before UPDATE
    _write(business_id, user_id, {"skipped": 1, "step_celebrated": 1})
    return get_state(business_id, user_id)


def reopen(business_id: str, user_id: str) -> Dict:
    """Undo skip — bring the wizard and checklist back."""
    _row(business_id, user_id)
    _write(business_id, user_id, {"skipped": 0, "step_celebrated": 0})
    return get_state(business_id, user_id)


# ── Profile extras (business_type / company_size / primary_goal) ─────────
# Persisted to business.settings.profile so other features can read them.
# The wizard ALSO embeds them in the description text for human readability,
# but settings.profile is the structured source of truth for code paths:
#   - apply_industry_setup reads primary_goal to tune which agents are featured
#   - team-invite UI hides itself when company_size = "1-5"
#   - dashboard KPI strip swaps based on primary_goal
import json as _json
from api.businesses import BUSINESSES_TABLE as _BIZ_TABLE


def set_profile_extras(business_id: str, *, business_type: str = "",
                       company_size: str = "", primary_goal: str = "") -> Dict[str, str]:
    """Merge profile extras into the business's settings JSON.

    Safe to call repeatedly — only non-empty values overwrite. Returns the
    final stored profile so the frontend can echo back what was saved.
    """
    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT settings FROM {_BIZ_TABLE} WHERE id = ?",
            (business_id,),
        ).fetchone()
        if not row:
            logger.warning(f"[Onboarding] set_profile_extras: business {business_id} not found")
            return {}
        try:
            settings = _json.loads(row[0] or "{}")
        except Exception:
            settings = {}
        profile = settings.get("profile") or {}
        if business_type:  profile["business_type"] = business_type.strip()
        if company_size:   profile["company_size"]  = company_size.strip()
        if primary_goal:   profile["primary_goal"]  = primary_goal.strip()
        settings["profile"] = profile
        conn.execute(
            f"UPDATE {_BIZ_TABLE} SET settings = ?, updated_at = ? WHERE id = ?",
            (_json.dumps(settings), now_iso(), business_id),
        )
        conn.commit()
        return profile
    finally:
        conn.close()


def get_profile_extras(business_id: str) -> Dict[str, str]:
    """Read the structured profile extras. Returns an empty dict if the
    business has nothing recorded yet."""
    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT settings FROM {_BIZ_TABLE} WHERE id = ?",
            (business_id,),
        ).fetchone()
        if not row:
            return {}
        try:
            settings = _json.loads(row[0] or "{}")
        except Exception:
            return {}
        return settings.get("profile") or {}
    finally:
        conn.close()
