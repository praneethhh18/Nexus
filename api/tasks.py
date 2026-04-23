"""
Tasks module — per-business to-dos with due dates, priority, status, and
optional linkage to CRM records (contacts/companies/deals).

All queries are scoped by business_id. The API layer resolves that via
get_current_context before calling into this module.
"""
from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from loguru import logger

from config.settings import DB_PATH

TASKS_TABLE = "nexus_tasks"

STATUSES = ("open", "in_progress", "done", "cancelled")
PRIORITIES = ("low", "normal", "high", "urgent")


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {TASKS_TABLE} "
            f"(id, business_id, title, description, status, priority, due_date, assignee_id, "
            f"contact_id, company_id, deal_id, tags, created_at, updated_at, completed_at, created_by) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row,
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
               "assignee_id", "contact_id", "company_id", "deal_id", "tags"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        raise HTTPException(400, "No editable fields provided")

    if "status" in fields and fields["status"] not in STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(STATUSES)}")
    if "priority" in fields and fields["priority"] not in PRIORITIES:
        raise HTTPException(400, f"Invalid priority. Must be one of: {', '.join(PRIORITIES)}")
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
