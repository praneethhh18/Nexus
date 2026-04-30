"""
Notification preferences + notification list/CRUD.

Two areas:
  - prefs: per-user toggles for which event types create a bell entry
  - list:  read/mark-read/delete the bell-icon items themselves

Note: the per-id mark-read endpoint is registered twice with the same path
pattern (different param name `notif_id` vs `nid`) — preserved as-is from
server.py to keep behaviour identical during the refactor.
"""
from __future__ import annotations

import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db

from fastapi import APIRouter, Depends

from api.auth import get_current_context
from api import notification_prefs as _notif_prefs

router = APIRouter(tags=["notifications"])


# ── Preferences ─────────────────────────────────────────────────────────────
@router.get("/api/notifications/prefs")
def notification_prefs_get(ctx: dict = Depends(get_current_context)):
    return _notif_prefs.get_prefs(ctx["user"]["id"])


@router.patch("/api/notifications/prefs")
def notification_prefs_set(body: dict, ctx: dict = Depends(get_current_context)):
    """Accepts {event_type: bool} pairs. Unknown keys are ignored."""
    return _notif_prefs.set_prefs(ctx["user"]["id"], body or {})


# ── Notification CRUD ───────────────────────────────────────────────────────
@router.get("/api/notifications")
def get_notifications(unread: bool = False, limit: int = 30,
                      ctx: dict = Depends(get_current_context)):
    from api.notifications import get_recent, get_unread_count
    return {
        "notifications": get_recent(business_id=ctx["business_id"], limit=limit, unread_only=unread),
        "unread_count": get_unread_count(business_id=ctx["business_id"]),
    }


@router.post("/api/notifications/{notif_id}/read")
def notifications_mark_one_read(notif_id: str, ctx: dict = Depends(get_current_context)):
    """Mark a single notification as read."""
    from api.notifications import mark_read
    mark_read(notif_id, business_id=ctx["business_id"])
    return {"ok": True}


# Historical duplicate of the above endpoint — registered with a different
# path-parameter name (`nid` vs `notif_id`). Preserved verbatim from server.py
# so route count and any client that targeted this exact handler continue to
# resolve identically.
@router.post("/api/notifications/{nid}/read")
def read_notification(nid: str, ctx: dict = Depends(get_current_context)):
    from api.notifications import mark_read
    mark_read(nid, business_id=ctx["business_id"])
    return {"ok": True}


@router.post("/api/notifications/read-all")
def read_all_notifications(ctx: dict = Depends(get_current_context)):
    from api.notifications import mark_all_read
    mark_all_read(business_id=ctx["business_id"])
    return {"ok": True}


@router.delete("/api/notifications/{notif_id}")
def notifications_delete_one(notif_id: str, ctx: dict = Depends(get_current_context)):
    """Remove a single notification."""
    from api.notifications import TABLE
    from config.db import get_conn
    conn = get_conn()
    try:
        conn.execute(
            f"DELETE FROM {TABLE} WHERE id = ? AND business_id = ?",
            (notif_id, ctx["business_id"]),
        )
        conn.commit()
    finally:
        conn.close()
    return {"ok": True}
