"""Per-task discussion thread: structured activity log + free-form comments.

Two tables, both append-only:

  nexus_task_activity
    Auto-emitted by api/tasks.py whenever something changes that the
    team would want to see in a history pane. Each row is structured
    ({kind, payload}) so the UI can render distinct events (status
    change, reassignment, due-date push) instead of a generic "edited".

  nexus_task_comments
    Free-form text from a user. Distinct from activity so a comment
    can be edited or deleted without rewriting history.

The UI fetches a merged feed via list_thread() that interleaves both
sources oldest-first, so a task's case-page reads top-to-bottom as a
conversation.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import HTTPException
from loguru import logger

from config.db import get_conn

ACTIVITY_TABLE = "nexus_task_activity"
COMMENTS_TABLE = "nexus_task_comments"

# Activity kinds: the controlled vocabulary the UI knows how to render.
# Extend deliberately, every new kind needs a UI affordance.
KIND_CREATED          = "created"
KIND_STATUS_CHANGED   = "status_changed"
KIND_ASSIGNED         = "assigned"        # from null to someone
KIND_REASSIGNED       = "reassigned"      # from someone to someone else
KIND_UNASSIGNED       = "unassigned"      # from someone to null
KIND_DUE_CHANGED      = "due_changed"
KIND_PRIORITY_CHANGED = "priority_changed"
KIND_COMPLETED        = "completed"
KIND_REOPENED         = "reopened"
KIND_COMMENTED        = "commented"       # synthetic — emitted by list_thread when merging comments


# ── Schema bootstrap ───────────────────────────────────────────────────────
def _conn():
    """Get a connection with both tables guaranteed to exist."""
    conn = get_conn()
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {ACTIVITY_TABLE} (
            id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            actor_id TEXT,
            kind TEXT NOT NULL,
            payload TEXT,
            created_at TEXT
        )
    """)
    conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_task_activity_task
        ON {ACTIVITY_TABLE}(task_id, created_at)
    """)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {COMMENTS_TABLE} (
            id TEXT PRIMARY KEY,
            business_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            author_id TEXT,
            body TEXT NOT NULL,
            created_at TEXT,
            updated_at TEXT
        )
    """)
    conn.execute(f"""
        CREATE INDEX IF NOT EXISTS idx_task_comments_task
        ON {COMMENTS_TABLE}(task_id, created_at)
    """)
    conn.commit()
    return conn


def _now() -> str:
    return datetime.now().isoformat()


# ── Activity ────────────────────────────────────────────────────────────────
def log_activity(
    business_id: str,
    task_id: str,
    actor_id: Optional[str],
    kind: str,
    payload: Optional[Dict[str, Any]] = None,
) -> str:
    """Append an activity row. Never raises — best-effort instrumentation
    must not break the underlying task mutation. Logs and swallows.

    Returns the new activity id, or '' on failure."""
    try:
        conn = _conn()
        aid = f"act-{uuid.uuid4().hex[:10]}"
        conn.execute(
            f"INSERT INTO {ACTIVITY_TABLE} "
            f"(id, business_id, task_id, actor_id, kind, payload, created_at) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?)",
            (aid, business_id, task_id, actor_id, kind,
             json.dumps(payload or {}, default=str), _now()),
        )
        conn.commit()
        conn.close()
        return aid
    except Exception as e:
        logger.warning(f"[task_threads] log_activity failed ({kind}): {e}")
        return ""


# ── Comments ────────────────────────────────────────────────────────────────
def add_comment(business_id: str, task_id: str, author_id: str, body: str) -> Dict[str, Any]:
    body = (body or "").strip()
    if not body:
        raise HTTPException(400, "Comment body is required")
    if len(body) > 4000:
        raise HTTPException(400, "Comment too long (max 4000 chars)")

    cid = f"cm-{uuid.uuid4().hex[:10]}"
    now = _now()
    conn = _conn()
    try:
        conn.execute(
            f"INSERT INTO {COMMENTS_TABLE} "
            f"(id, business_id, task_id, author_id, body, created_at, updated_at) "
            f"VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cid, business_id, task_id, author_id, body, now, now),
        )
        conn.commit()
    finally:
        conn.close()

    # Also fire a notification to the assignee if someone else commented.
    # Comment-on-task is a real signal that the assignee should look at.
    try:
        from api import tasks as _tasks
        from api import notifications as _notifs
        t = _tasks.get_task(business_id, task_id)
        assignee = t.get("assignee_id")
        if assignee and assignee != author_id:
            _notifs.push(
                business_id=business_id,
                user_id=assignee,
                title=f"New comment on: {(t.get('title') or '')[:80]}",
                message=body[:160],
                severity="info",
                type="task_commented",
                metadata={"task_id": task_id, "comment_id": cid,
                          "link": f"/tasks/{task_id}"},
            )
    except Exception as e:
        logger.debug(f"[task_threads] comment notification skipped: {e}")

    return {
        "id": cid, "task_id": task_id, "author_id": author_id,
        "body": body, "created_at": now, "updated_at": now,
    }


def delete_comment(business_id: str, comment_id: str, actor_id: str) -> bool:
    """Authors can delete their own comments. Owners/admins can delete
    anyone's. Returns True if deleted, False if not found / not allowed."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT author_id FROM {COMMENTS_TABLE} "
            f"WHERE id = ? AND business_id = ?",
            (comment_id, business_id),
        ).fetchone()
        if not row:
            return False
        # The HTTP layer is responsible for role enforcement; here we
        # only enforce "author can delete their own". The router will
        # bypass this for managers/owners by passing actor_id=None.
        if actor_id and row["author_id"] != actor_id:
            return False
        conn.execute(
            f"DELETE FROM {COMMENTS_TABLE} WHERE id = ? AND business_id = ?",
            (comment_id, business_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()


# ── Merged thread ───────────────────────────────────────────────────────────
def list_thread(business_id: str, task_id: str) -> List[Dict[str, Any]]:
    """Return activity + comments interleaved oldest-first.

    Each entry has the shape:
      { id, kind, actor_id, body, payload, created_at }

    Where `kind` is one of the KIND_* constants (or 'commented' for
    comment rows), and `body` carries the comment text for comments
    (empty for activity rows). `payload` is the structured diff for
    activity rows (e.g. {'from': 'open', 'to': 'in_progress'}).

    The frontend uses `kind` to pick an icon + verb phrase ("Praneeth
    assigned this to Anuj") and falls back to a generic line for any
    unknown kind."""
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        acts = conn.execute(
            f"SELECT id, actor_id, kind, payload, created_at "
            f"FROM {ACTIVITY_TABLE} "
            f"WHERE business_id = ? AND task_id = ? "
            f"ORDER BY created_at ASC",
            (business_id, task_id),
        ).fetchall()
        comms = conn.execute(
            f"SELECT id, author_id, body, created_at, updated_at "
            f"FROM {COMMENTS_TABLE} "
            f"WHERE business_id = ? AND task_id = ? "
            f"ORDER BY created_at ASC",
            (business_id, task_id),
        ).fetchall()
    finally:
        conn.close()

    out: List[Dict[str, Any]] = []
    for a in acts:
        try:
            payload = json.loads(a["payload"]) if a["payload"] else {}
        except Exception:
            payload = {}
        out.append({
            "id":         a["id"],
            "kind":       a["kind"],
            "actor_id":   a["actor_id"],
            "body":       "",
            "payload":    payload,
            "created_at": a["created_at"],
        })
    for c in comms:
        out.append({
            "id":         c["id"],
            "kind":       KIND_COMMENTED,
            "actor_id":   c["author_id"],
            "body":       c["body"],
            "payload":    {},
            "created_at": c["created_at"],
            "updated_at": c["updated_at"],
        })

    out.sort(key=lambda e: e["created_at"] or "")
    return out
