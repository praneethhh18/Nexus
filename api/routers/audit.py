"""
Audit-log browse + CSV export. Admin/owner only — the log holds every
tool call, approval decision, and error message for the current business.
"""
from __future__ import annotations

import csv
import io
import sqlite3 as _sq
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from api.auth import get_current_context
from config.settings import DB_PATH

router = APIRouter(tags=["audit"])


@router.get("/api/audit")
def audit_log_list(
    limit: int = 100,
    tool: Optional[str] = None,
    user_id_filter: Optional[str] = None,
    success: Optional[bool] = None,
    search: Optional[str] = None,
    ctx: dict = Depends(get_current_context),
):
    """Admin/owner can view the full audit log for the current business."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can view the audit log")

    limit = max(1, min(limit, 1000))
    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row
    try:
        sql = ("SELECT event_id, timestamp, event_type, tool_name, input_summary, "
               "output_summary, duration_ms, human_approved, success, error_message, "
               "business_id, user_id FROM nexus_audit_log WHERE business_id = ?")
        params: list = [ctx["business_id"]]
        if tool:
            sql += " AND tool_name LIKE ?"; params.append(f"%{tool}%")
        if user_id_filter:
            sql += " AND user_id = ?"; params.append(user_id_filter)
        if success is not None:
            sql += " AND success = ?"; params.append(1 if success else 0)
        if search:
            sql += " AND (input_summary LIKE ? OR output_summary LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        rows = [dict(r) for r in conn.execute(sql, params).fetchall()]
    finally:
        conn.close()

    # Enrich with actor name so the UI doesn't have to re-query per row.
    user_ids = {r["user_id"] for r in rows if r.get("user_id")}
    names: dict = {}
    if user_ids:
        conn = _sq.connect(DB_PATH)
        conn.row_factory = _sq.Row
        try:
            placeholders = ",".join("?" for _ in user_ids)
            for r in conn.execute(
                f"SELECT id, name, email FROM nexus_users WHERE id IN ({placeholders})",
                tuple(user_ids),
            ).fetchall():
                names[r["id"]] = r["name"] or r["email"]
        finally:
            conn.close()
    for r in rows:
        r["actor_name"] = names.get(r.get("user_id"), r.get("user_id") or "system")
    return rows


@router.get("/api/audit/export")
def audit_log_export_csv(
    limit: int = 5000,
    ctx: dict = Depends(get_current_context),
):
    """CSV export of the audit log. Admin/owner only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can export the audit log")

    limit = max(1, min(limit, 100000))
    conn = _sq.connect(DB_PATH)
    conn.row_factory = _sq.Row
    try:
        rows = conn.execute(
            "SELECT event_id, timestamp, event_type, tool_name, user_id, "
            "input_summary, output_summary, duration_ms, human_approved, success, "
            "error_message FROM nexus_audit_log WHERE business_id = ? "
            "ORDER BY timestamp DESC LIMIT ?",
            (ctx["business_id"], limit),
        ).fetchall()
    finally:
        conn.close()
    buf = io.StringIO()
    if rows:
        w = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows:
            w.writerow(dict(r))
    return Response(
        content=buf.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_log.csv"},
    )
