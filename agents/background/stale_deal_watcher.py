"""
Stale-deal watcher — every business day at 08:30, find deals that have not
moved for more than STALE_THRESHOLD_DAYS and queue a follow-up task.

Safe by design:
- Only creates tasks (reversible, low-risk). Never emails customers directly.
- Idempotent per deal+day — we won't create duplicate follow-up tasks on
  successive runs.
- Per-business opt-out via the `stale_deal_watcher.enabled` memory flag.
"""
from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

from loguru import logger

from config.settings import DB_PATH

STALE_THRESHOLD_DAYS = int(os.getenv("STALE_DEAL_DAYS", "14"))
AGENT_TAG = "stale-deal-watcher"


def _opt_out(business_id: str) -> bool:
    """Skip if the user has explicitly disabled this agent in memory."""
    from agents.business_memory import list_memory
    try:
        items = list_memory(business_id, search="stale_deal_watcher", limit=5)
    except Exception:
        return False
    for it in items:
        c = (it.get("content") or "").lower()
        if "stale_deal_watcher" in c and ("disabled" in c or "off" in c or "opt out" in c):
            return True
    return False


def _already_handled_today(business_id: str, deal_id: str) -> bool:
    """Check whether we've already created a follow-up task for this deal today."""
    from api.tasks import TASKS_TABLE
    today = datetime.utcnow().date().isoformat()
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            f"SELECT 1 FROM {TASKS_TABLE} WHERE business_id = ? AND deal_id = ? "
            f"AND tags LIKE ? AND DATE(created_at) = ? LIMIT 1",
            (business_id, deal_id, f"%{AGENT_TAG}%", today),
        ).fetchone()
    finally:
        conn.close()
    return bool(row)


def run_for_business(business_id: str) -> dict:
    """Scan the deal pipeline for this business and queue follow-ups."""
    from api import crm as _crm
    from api import tasks as _tasks
    from api import notifications as _notifs

    if _opt_out(business_id):
        return {"business_id": business_id, "skipped": True, "created": 0}

    # Find open deals in non-terminal stages
    threshold = datetime.utcnow() - timedelta(days=STALE_THRESHOLD_DAYS)
    stale = []
    for stage in ("lead", "qualified", "proposal", "negotiation"):
        for d in _crm.list_deals(business_id, stage=stage, limit=200):
            try:
                updated = datetime.fromisoformat(d["updated_at"])
            except Exception:
                continue
            if updated < threshold:
                stale.append(d)

    created = 0
    for d in stale:
        if _already_handled_today(business_id, d["id"]):
            continue
        title = f"Follow up: {d['name']} ({d['stage']})"
        days_stale = (datetime.utcnow() - datetime.fromisoformat(d["updated_at"])).days
        description = (
            f"This deal has not moved for {days_stale} days. "
            f"Current stage: {d['stage']}, value: {d.get('value', 0)} {d.get('currency', 'USD')}. "
            f"Consider reaching out or re-qualifying."
        )
        try:
            _tasks.create_task(business_id, d.get("created_by") or "system", {
                "title": title,
                "description": description,
                "priority": "normal",
                "status": "open",
                "tags": AGENT_TAG,
                "deal_id": d["id"],
                "contact_id": d.get("contact_id"),
                "company_id": d.get("company_id"),
            })
            created += 1
        except Exception as e:
            logger.warning(f"[StaleWatcher] Could not create task for deal {d['id']}: {e}")

    if created:
        try:
            _notifs.push(
                title="Stale deals need attention",
                message=f"{created} deal{'s' if created != 1 else ''} haven't moved in {STALE_THRESHOLD_DAYS}+ days. Follow-up tasks created.",
                severity="warning",
                type="agent",
                business_id=business_id,
            )
        except Exception:
            pass

    logger.info(f"[StaleWatcher] biz={business_id} stale={len(stale)} tasks_created={created}")
    return {"business_id": business_id, "stale_deals": len(stale), "created": created}


def run_for_all_businesses() -> list:
    """Iterate over all active businesses and run the watcher."""
    from api.businesses import BUSINESSES_TABLE
    results = []
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            f"SELECT id FROM {BUSINESSES_TABLE} WHERE is_active = 1",
        ).fetchall()
    finally:
        conn.close()
    for r in rows:
        try:
            results.append(run_for_business(r["id"]))
        except Exception as e:
            logger.warning(f"[StaleWatcher] Failed for {r['id']}: {e}")
            results.append({"business_id": r["id"], "error": str(e)})
    return results
