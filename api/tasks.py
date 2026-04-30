"""
Tasks module — per-business to-dos with due dates, priority, status, and
optional linkage to CRM records (contacts/companies/deals).

All queries are scoped by business_id. The API layer resolves that via
get_current_context before calling into this module.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from loguru import logger

from config.db import get_conn, list_columns

TASKS_TABLE = "nexus_tasks"

STATUSES = ("open", "in_progress", "done", "cancelled")
PRIORITIES = ("low", "normal", "high", "urgent")
RECURRENCES = ("none", "daily", "weekly", "monthly")


def _get_conn():
    conn = get_conn()
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {TASKS_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT DEFAULT 'open',
        priority TEXT DEFAULT 'normal',
        due_date TEXT,
        assignee_id TEXT,
        contact_id TEXT,
        company_id TEXT,
        deal_id TEXT,
        tags TEXT DEFAULT '',
        created_at TEXT,
        updated_at TEXT,
        completed_at TEXT,
        created_by TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_tasks_biz ON {TASKS_TABLE}(business_id, status, due_date)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_tasks_assignee ON {TASKS_TABLE}(assignee_id)")
    # Additive migrations for recurring tasks — safe to re-run.
    for col, decl in [
        ("recurrence", "TEXT DEFAULT 'none'"),
        ("recurrence_parent_id", "TEXT"),
    ]:
        existing = list_columns(conn, TASKS_TABLE)
        if col not in existing:
            conn.execute(f"ALTER TABLE {TASKS_TABLE} ADD COLUMN {col} {decl}")
    conn.commit()
    return conn


def _validate_text(val: str, field: str, max_len: int = 400) -> str:
    val = (val or "").strip()
    if len(val) > max_len:
        raise HTTPException(400, f"{field} too long (max {max_len} chars)")
    return val


def _now() -> str:
    return datetime.now().isoformat()


def _validate_due_date(s: Optional[str]) -> Optional[str]:
    """Accept YYYY-MM-DD or full ISO; store as ISO date string."""
    if not s:
        return None
    s = s.strip()
    try:
        if len(s) == 10:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        # try full isoformat
        parsed = datetime.fromisoformat(s.replace("Z", "+00:00"))
        return parsed.date().isoformat()
    except Exception:
        raise HTTPException(400, f"Invalid due_date format: {s} (use YYYY-MM-DD)")


# ═══════════════════════════════════════════════════════════════════════════════
#  CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def create_task(business_id: str, user_id: str, data: Dict[str, Any]) -> Dict:
    title = _validate_text(data.get("title", ""), "Title", 200)
    if not title:
        raise HTTPException(400, "Task title is required")

    status = data.get("status", "open")
    if status not in STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(STATUSES)}")

    priority = data.get("priority", "normal")
    if priority not in PRIORITIES:
        raise HTTPException(400, f"Invalid priority. Must be one of: {', '.join(PRIORITIES)}")

    due = _validate_due_date(data.get("due_date"))

    recurrence = (data.get("recurrence") or "none").strip().lower()
    if recurrence not in RECURRENCES:
        raise HTTPException(400, f"Invalid recurrence. Must be one of: {', '.join(RECURRENCES)}")
    recurrence_parent_id = data.get("recurrence_parent_id") or None

    # Optional CRM links — only validate if present
    from api import crm as _crm
    contact_id = data.get("contact_id") or None
    company_id = data.get("company_id") or None
    deal_id = data.get("deal_id") or None
    if contact_id:
        _crm.get_contact(business_id, contact_id)
    if company_id:
        _crm.get_company(business_id, company_id)
    if deal_id:
        _crm.get_deal(business_id, deal_id)

    # assignee_id is validated at the API layer (must be a business member)
    assignee_id = data.get("assignee_id") or user_id

    tid = f"tk-{uuid.uuid4().hex[:10]}"
    row = (
        tid, business_id, title,
        _validate_text(data.get("description", ""), "Description", 4000),
        status, priority, due, assignee_id,
        contact_id, company_id, deal_id,
        _validate_text(data.get("tags", ""), "Tags", 300),
        _now(), _now(), None, user_id,
        recurrence, recurrence_parent_id,
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {TASKS_TABLE} "
            f"(id, business_id, title, description, status, priority, due_date, assignee_id, "
            f"contact_id, company_id, deal_id, tags, created_at, updated_at, completed_at, created_by, "
            f"recurrence, recurrence_parent_id) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row,
        )
        conn.commit()
    finally:
        conn.close()

    # Fire-and-forget mention processing on title + description
    try:
        from api.team import process_mentions
        mention_text = f"{title}\n{data.get('description', '') or ''}"
        process_mentions(
            business_id=business_id, author_id=user_id, text=mention_text,
            context_label=f"task '{title[:60]}'",
        )
    except Exception:
        pass

    return get_task(business_id, tid)


def get_task(business_id: str, task_id: str) -> Dict:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {TASKS_TABLE} WHERE id = ? AND business_id = ?",
            (task_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Task not found")
    return dict(row)


def list_tasks(
    business_id: str,
    status: Optional[str] = None,
    assignee_id: Optional[str] = None,
    search: Optional[str] = None,
    due_window: Optional[str] = None,
    limit: int = 200,
) -> List[Dict]:
    """
    due_window: 'overdue' | 'today' | 'this_week' | None
    """
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        sql = f"SELECT * FROM {TASKS_TABLE} WHERE business_id = ?"
        params: list = [business_id]

        if status:
            if status not in STATUSES and status != "active":
                raise HTTPException(400, f"Invalid status: {status}")
            if status == "active":
                sql += " AND status IN ('open', 'in_progress')"
            else:
                sql += " AND status = ?"
                params.append(status)

        if assignee_id:
            sql += " AND assignee_id = ?"
            params.append(assignee_id)

        if search:
            sql += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])

        today = date.today().isoformat()
        if due_window == "overdue":
            sql += " AND due_date IS NOT NULL AND due_date < ? AND status NOT IN ('done','cancelled')"
            params.append(today)
        elif due_window == "today":
            sql += " AND due_date = ?"
            params.append(today)
        elif due_window == "this_week":
            end = (date.today() + timedelta(days=7)).isoformat()
            sql += " AND due_date IS NOT NULL AND due_date >= ? AND due_date <= ?"
            params.extend([today, end])

        sql += " ORDER BY CASE WHEN status IN ('done','cancelled') THEN 1 ELSE 0 END, " \
               "CASE priority WHEN 'urgent' THEN 1 WHEN 'high' THEN 2 WHEN 'normal' THEN 3 ELSE 4 END, " \
               "due_date ASC, created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


def update_task(business_id: str, task_id: str, updates: Dict[str, Any]) -> Dict:
    get_task(business_id, task_id)
    allowed = {"title", "description", "status", "priority", "due_date",
               "assignee_id", "contact_id", "company_id", "deal_id", "tags",
               "recurrence"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        raise HTTPException(400, "No editable fields provided")

    if "status" in fields and fields["status"] not in STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(STATUSES)}")
    if "priority" in fields and fields["priority"] not in PRIORITIES:
        raise HTTPException(400, f"Invalid priority. Must be one of: {', '.join(PRIORITIES)}")
    if "recurrence" in fields:
        fields["recurrence"] = (fields["recurrence"] or "none").strip().lower()
        if fields["recurrence"] not in RECURRENCES:
            raise HTTPException(400, f"Invalid recurrence. Must be one of: {', '.join(RECURRENCES)}")
    if "due_date" in fields:
        fields["due_date"] = _validate_due_date(fields["due_date"])
    if "title" in fields:
        fields["title"] = _validate_text(fields["title"], "Title", 200)
    if "description" in fields:
        fields["description"] = _validate_text(fields["description"], "Description", 4000)

    # Validate CRM links
    from api import crm as _crm
    if fields.get("contact_id"):
        _crm.get_contact(business_id, fields["contact_id"])
    if fields.get("company_id"):
        _crm.get_company(business_id, fields["company_id"])
    if fields.get("deal_id"):
        _crm.get_deal(business_id, fields["deal_id"])

    # Auto-stamp completed_at when transitioning to done
    extra_sets = []
    extra_params: list = []
    if fields.get("status") == "done":
        extra_sets.append("completed_at = ?")
        extra_params.append(_now())
    elif "status" in fields and fields["status"] != "done":
        extra_sets.append("completed_at = NULL")

    sets = ", ".join(f"{k} = ?" for k in fields)
    if extra_sets:
        sets += ", " + ", ".join(extra_sets)
    params = list(fields.values()) + extra_params + [_now(), task_id, business_id]

    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {TASKS_TABLE} SET {sets}, updated_at = ? WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()

    # If this update just marked a recurring task as done, spawn the next
    # occurrence so the user doesn't have to re-create it manually.
    if fields.get("status") == "done":
        try:
            spawn_next_if_recurring(business_id, task_id)
        except Exception as e:
            logger.warning(f"[tasks] spawn_next_if_recurring failed for {task_id}: {e}")

    return get_task(business_id, task_id)


def delete_task(business_id: str, task_id: str) -> None:
    get_task(business_id, task_id)
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {TASKS_TABLE} WHERE id = ? AND business_id = ?", (task_id, business_id))
        conn.commit()
    finally:
        conn.close()


def task_summary(business_id: str, user_id: Optional[str] = None) -> Dict[str, Any]:
    """Dashboard summary: counts by bucket (today, overdue, upcoming, done_today)."""
    conn = _get_conn()
    try:
        today = date.today().isoformat()
        end_week = (date.today() + timedelta(days=7)).isoformat()

        def _q(where: str, params: tuple) -> int:
            return conn.execute(
                f"SELECT COUNT(*) FROM {TASKS_TABLE} WHERE business_id = ? {where}",
                (business_id,) + params,
            ).fetchone()[0]

        # Optionally narrow by assignee
        assignee_clause = ""
        assignee_params: tuple = ()
        if user_id:
            assignee_clause = "AND assignee_id = ?"
            assignee_params = (user_id,)

        overdue = _q(
            f"{assignee_clause} AND due_date < ? AND status NOT IN ('done','cancelled')",
            assignee_params + (today,),
        )
        today_count = _q(
            f"{assignee_clause} AND due_date = ? AND status NOT IN ('done','cancelled')",
            assignee_params + (today,),
        )
        upcoming = _q(
            f"{assignee_clause} AND due_date > ? AND due_date <= ? AND status NOT IN ('done','cancelled')",
            assignee_params + (today, end_week),
        )
        open_total = _q(
            f"{assignee_clause} AND status IN ('open','in_progress')",
            assignee_params,
        )
        done_today = _q(
            f"{assignee_clause} AND status = 'done' AND completed_at >= ?",
            assignee_params + (today + "T00:00:00",),
        )
    finally:
        conn.close()
    return {
        "overdue": overdue,
        "today": today_count,
        "upcoming": upcoming,
        "open_total": open_total,
        "done_today": done_today,
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Bulk helpers — used by the list-page bulk action bar
# ═══════════════════════════════════════════════════════════════════════════════
def bulk_delete(business_id: str, task_ids: List[str]) -> int:
    """Delete many tasks in one transaction. Returns count actually removed."""
    if not task_ids:
        return 0
    placeholders = ",".join("?" for _ in task_ids)
    conn = _get_conn()
    try:
        cur = conn.execute(
            f"DELETE FROM {TASKS_TABLE} "
            f"WHERE business_id = ? AND id IN ({placeholders})",
            [business_id, *task_ids],
        )
        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()


def bulk_update_status(business_id: str, task_ids: List[str], status: str) -> int:
    """Change status on many tasks. Useful for 'mark selected as done'."""
    if status not in STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(STATUSES)}")
    if not task_ids:
        return 0
    placeholders = ",".join("?" for _ in task_ids)
    completed_clause = ", completed_at = ?" if status == "done" else (
        ", completed_at = NULL" if status != "done" else ""
    )
    params: List = [status, _now()]
    if status == "done":
        params.append(_now())
    params += [business_id, *task_ids]
    conn = _get_conn()
    try:
        cur = conn.execute(
            f"UPDATE {TASKS_TABLE} SET status = ?, updated_at = ?{completed_clause} "
            f"WHERE business_id = ? AND id IN ({placeholders})",
            params,
        )
        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  Recurrence — spawn the next occurrence when the current one is marked done
# ═══════════════════════════════════════════════════════════════════════════════
def _next_due(current_due: Optional[str], recurrence: str) -> Optional[str]:
    """Compute the due date for the next occurrence. None means 'no next'."""
    if recurrence == "none" or not current_due:
        return None
    try:
        d = date.fromisoformat(current_due)
    except Exception:
        return None
    if recurrence == "daily":
        return (d + timedelta(days=1)).isoformat()
    if recurrence == "weekly":
        return (d + timedelta(days=7)).isoformat()
    if recurrence == "monthly":
        # Naïve but correct for 99% of cases: jump 30 days forward.
        return (d + timedelta(days=30)).isoformat()
    return None


def spawn_next_if_recurring(business_id: str, completed_task_id: str) -> Optional[Dict]:
    """
    If `completed_task_id` is part of a recurring series and has just been
    marked done, create the next occurrence with the same shape. Returns the
    new task or None. Idempotent — won't create duplicates if called twice.
    """
    src = get_task(business_id, completed_task_id)
    recurrence = (src.get("recurrence") or "none").lower()
    if recurrence == "none":
        return None
    if src.get("status") != "done":
        return None
    # Parent id chain: root task's id is reused as parent for all children.
    parent_id = src.get("recurrence_parent_id") or src["id"]
    # Has a pending next already been created?
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        existing = conn.execute(
            f"SELECT id FROM {TASKS_TABLE} "
            f"WHERE business_id = ? AND recurrence_parent_id = ? AND status IN ('open','in_progress')",
            (business_id, parent_id),
        ).fetchone()
    finally:
        conn.close()
    if existing:
        return None
    next_due = _next_due(src.get("due_date"), recurrence)
    spawn_data = {
        "title": src["title"],
        "description": src.get("description", ""),
        "status": "open",
        "priority": src.get("priority", "normal"),
        "due_date": next_due,
        "assignee_id": src.get("assignee_id"),
        "contact_id": src.get("contact_id"),
        "company_id": src.get("company_id"),
        "deal_id": src.get("deal_id"),
        "tags": src.get("tags", ""),
        "recurrence": recurrence,
        "recurrence_parent_id": parent_id,
    }
    return create_task(business_id, src.get("created_by") or "system", spawn_data)
