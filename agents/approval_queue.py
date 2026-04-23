"""
Approval queue — pending agent actions that need human sign-off before execution.

Every write tool that is marked `requires_approval` gets routed here instead of
executing immediately. The user sees it on the Approvals page and can approve
(→ action runs, result stored) or reject (→ no action, just logged).

Security:
- Every action is strictly scoped to a business_id; only members of that
  business can list/approve/reject.
- The `args_json` is stored as-is but validated by the tool handler when
  approval is granted (defence in depth — don't trust stored data blindly).
- Rejections are permanent; approvals are one-shot.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from loguru import logger

from config.settings import DB_PATH

APPROVALS_TABLE = "nexus_agent_approvals"

STATUSES = ("pending", "approved", "rejected", "expired", "executed", "failed")


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {APPROVALS_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        requested_by TEXT NOT NULL,
        tool_name TEXT NOT NULL,
        summary TEXT,
        args_json TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        created_at TEXT NOT NULL,
        expires_at TEXT,
        decided_by TEXT,
        decided_at TEXT,
        executed_at TEXT,
        result_json TEXT,
        error TEXT
    )""")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_appr_biz_status "
                 f"ON {APPROVALS_TABLE}(business_id, status, created_at)")
    conn.commit()
    return conn


def _now() -> str:
    return datetime.utcnow().isoformat()


# ── Queue operations ────────────────────────────────────────────────────────
def queue_action(
    business_id: str,
    user_id: str,
    tool_name: str,
    summary: str,
    args: Dict[str, Any],
    ttl_hours: int = 24,
) -> Dict[str, Any]:
    """Create a pending action and return the full record."""
    aid = f"ap-{uuid.uuid4().hex[:10]}"
    created = datetime.utcnow()
    expires = created + timedelta(hours=max(1, min(ttl_hours, 720)))
    row = (
        aid, business_id, user_id, tool_name,
        (summary or "")[:500],
        json.dumps(args or {}, default=str),
        "pending",
        created.isoformat(),
        expires.isoformat(),
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {APPROVALS_TABLE} "
            f"(id, business_id, requested_by, tool_name, summary, args_json, "
            f"status, created_at, expires_at) VALUES (?,?,?,?,?,?,?,?,?)", row,
        )
        conn.commit()
    finally:
        conn.close()
    logger.info(f"[Approvals] Queued {tool_name} id={aid} biz={business_id}")
    return get_action(business_id, aid)


def get_action(business_id: str, action_id: str) -> Dict[str, Any]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {APPROVALS_TABLE} WHERE id = ? AND business_id = ?",
            (action_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Pending action not found")
    d = dict(row)
    d["args"] = json.loads(d.pop("args_json") or "{}")
    if d.get("result_json"):
        try:
            d["result"] = json.loads(d.pop("result_json"))
        except Exception:
            d["result"] = None
    return d


def list_actions(
    business_id: str,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        # Auto-expire stale pending rows
        now = _now()
        conn.execute(
            f"UPDATE {APPROVALS_TABLE} SET status = 'expired' "
            f"WHERE business_id = ? AND status = 'pending' AND expires_at < ?",
            (business_id, now),
        )
        conn.commit()

        sql = f"SELECT * FROM {APPROVALS_TABLE} WHERE business_id = ?"
        params: list = [business_id]
        if status:
            if status not in STATUSES:
                raise HTTPException(400, f"Invalid status: {status}")
            sql += " AND status = ?"
            params.append(status)
        sql += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["args"] = json.loads(d.pop("args_json") or "{}")
        except Exception:
            d["args"] = {}
        if d.get("result_json"):
            try:
                d["result"] = json.loads(d.pop("result_json"))
            except Exception:
                d["result"] = None
        result.append(d)
    return result


def pending_count(business_id: str) -> int:
    conn = _get_conn()
    try:
        row = conn.execute(
            f"SELECT COUNT(*) FROM {APPROVALS_TABLE} "
            f"WHERE business_id = ? AND status = 'pending'",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    return int(row[0] or 0)


def _update_status(action_id: str, business_id: str, status: str, **extras) -> None:
    conn = _get_conn()
    try:
        sets = ["status = ?"]
        params: list = [status]
        for k, v in extras.items():
            sets.append(f"{k} = ?")
            params.append(v)
        params.extend([action_id, business_id])
        conn.execute(
            f"UPDATE {APPROVALS_TABLE} SET {', '.join(sets)} WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()


def approve_action(business_id: str, user_id: str, action_id: str) -> Dict[str, Any]:
    """Approve and execute the action. Returns the updated action with result."""
    action = get_action(business_id, action_id)
    if action["status"] != "pending":
        raise HTTPException(400, f"Action is already {action['status']}")

    # Re-check expiry
    try:
        expires = datetime.fromisoformat(action["expires_at"])
    except Exception:
        expires = datetime.utcnow()
    if datetime.utcnow() > expires:
        _update_status(action_id, business_id, "expired")
        raise HTTPException(400, "Action has expired")

    _update_status(action_id, business_id, "approved", decided_by=user_id, decided_at=_now())

    # Execute
    from agents.tool_registry import execute_tool_now
    try:
        result = execute_tool_now(
            tool_name=action["tool_name"],
            arguments=action["args"],
            business_id=business_id,
            user_id=user_id,
        )
        _update_status(
            action_id, business_id, "executed",
            executed_at=_now(),
            result_json=json.dumps(result, default=str)[:20000],
        )
        logger.info(f"[Approvals] Executed {action['tool_name']} id={action_id}")
    except Exception as e:
        _update_status(
            action_id, business_id, "failed",
            executed_at=_now(),
            error=str(e)[:500],
        )
        logger.error(f"[Approvals] Execution failed for {action_id}: {e}")
        raise HTTPException(500, f"Execution failed: {e}")

    return get_action(business_id, action_id)


def reject_action(business_id: str, user_id: str, action_id: str, reason: str = "") -> Dict[str, Any]:
    action = get_action(business_id, action_id)
    if action["status"] != "pending":
        raise HTTPException(400, f"Action is already {action['status']}")
    _update_status(
        action_id, business_id, "rejected",
        decided_by=user_id, decided_at=_now(),
        error=(reason or "")[:500],
    )
    return get_action(business_id, action_id)
