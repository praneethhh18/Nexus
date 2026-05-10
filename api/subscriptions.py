"""Subscription state — persists what plan each business is on.

Writes happen at exactly one place: `record_payment()`, called from
api/routers/billing.py after the HMAC signature on a Razorpay payment is
verified. Reads happen anywhere the app needs to gate a feature by tier.

Schema lives in db/migrations/0005_subscriptions.sql:
    nexus_subscriptions       — one row per business, current state
    nexus_subscription_events — append-only audit log

Rules:
  * `record_payment()` is idempotent on (razorpay_payment_id) so a duplicate
    webhook delivery doesn't double-extend the subscription.
  * `current_period_end` is set to NOW + 30 days for monthly plans, NOW + 1
    year for the (eventual) annual plans, NULL for one-time purchases.
  * `business.plan` is the authoritative read — Razorpay's dashboard is the
    audit trail, not the source of truth.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from loguru import logger

from config.db import get_conn, is_postgres
from utils.timez import now_iso


def _ph() -> str:
    """Param placeholder for the active backend."""
    return "%s" if is_postgres() else "?"


def _period_end_for(plan_key: str) -> Optional[str]:
    """When does this billing cycle end? None for one-time / Free / unknown."""
    from api.routers.billing import PLANS
    plan = PLANS.get(plan_key) or {}
    period = plan.get("period")
    if period == "monthly":
        return (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
    if period == "annual":
        return (datetime.now(timezone.utc) + timedelta(days=365)).isoformat()
    return None


def get_subscription(business_id: str) -> Dict[str, Any]:
    """Read current state. Always returns a dict — falls back to the free
    tier shape if no row exists, so callers don't have to None-guard."""
    if not business_id:
        return {"business_id": "", "plan": "free", "status": "active"}
    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT business_id, plan, status, started_at, current_period_end, "
            f"razorpay_customer_id, razorpay_subscription_id, last_payment_id, "
            f"updated_at FROM nexus_subscriptions WHERE business_id = {_ph()}",
            (business_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return {
            "business_id":           business_id,
            "plan":                  "free",
            "status":                "active",
            "started_at":            None,
            "current_period_end":    None,
            "last_payment_id":       None,
        }
    return dict(row) if hasattr(row, "keys") else {
        "business_id":           row[0],
        "plan":                  row[1],
        "status":                row[2],
        "started_at":            row[3],
        "current_period_end":    row[4],
        "razorpay_customer_id":  row[5],
        "razorpay_subscription_id": row[6],
        "last_payment_id":       row[7],
        "updated_at":            row[8],
    }


def get_plan(business_id: str) -> str:
    """Convenience — just the plan key. Used by feature gates throughout
    the codebase: `if check_plan(get_plan(biz), 'pro'): ...`"""
    return (get_subscription(business_id) or {}).get("plan") or "free"


def record_payment(
    *,
    business_id: str,
    plan: str,
    amount_paise: int,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    event_type: str = "payment_verified",
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Mark a payment as recorded and (re)set the business's subscription
    to the paid tier. Idempotent on razorpay_payment_id — a re-delivered
    webhook is safe to call.

    Returns the updated subscription row."""
    if not business_id or not plan or not razorpay_payment_id:
        raise ValueError("business_id, plan, razorpay_payment_id are all required")

    # 1. Audit-log the event first. If anything below fails we still have
    #    the receipt that something was attempted.
    conn = get_conn()
    try:
        already = conn.execute(
            f"SELECT 1 FROM nexus_subscription_events "
            f"WHERE razorpay_payment_id = {_ph()} AND event_type = {_ph()} LIMIT 1",
            (razorpay_payment_id, event_type),
        ).fetchone()
        if already:
            logger.info(f"[subscriptions] duplicate {event_type} for payment "
                        f"{razorpay_payment_id} — ignored")
            conn.close()
            return get_subscription(business_id)

        conn.execute(
            f"INSERT INTO nexus_subscription_events "
            f"(business_id, event_type, plan, amount_paise, "
            f" razorpay_order_id, razorpay_payment_id, payload_json, created_at) "
            f"VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
            (
                business_id, event_type, plan, amount_paise,
                razorpay_order_id, razorpay_payment_id,
                json.dumps(extra_payload or {}), now_iso(),
            ),
        )
        conn.commit()
    finally:
        conn.close()

    # 2. Upsert the current-state row. Postgres ON CONFLICT works here, the
    #    SQLite path uses the same syntax (supported since 3.24).
    started_at = now_iso()
    period_end = _period_end_for(plan)
    conn = get_conn()
    try:
        conn.execute(
            f"INSERT INTO nexus_subscriptions "
            f"(business_id, plan, status, started_at, current_period_end, "
            f" last_payment_id, updated_at) "
            f"VALUES ({_ph()}, {_ph()}, 'active', {_ph()}, {_ph()}, {_ph()}, {_ph()}) "
            f"ON CONFLICT(business_id) DO UPDATE SET "
            f"  plan = excluded.plan, "
            f"  status = 'active', "
            f"  started_at = excluded.started_at, "
            f"  current_period_end = excluded.current_period_end, "
            f"  last_payment_id = excluded.last_payment_id, "
            f"  updated_at = excluded.updated_at",
            (business_id, plan, started_at, period_end, razorpay_payment_id, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()

    logger.success(
        f"[subscriptions] biz={business_id} -> {plan} "
        f"period_end={period_end} payment={razorpay_payment_id}"
    )
    return get_subscription(business_id)


def record_event(
    *,
    business_id: str,
    event_type: str,
    plan: Optional[str] = None,
    amount_paise: int = 0,
    razorpay_order_id: Optional[str] = None,
    razorpay_payment_id: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """Append-only audit log writer. Use for non-money events
    (subscription cancelled, plan downgraded, refund, webhook noise)."""
    conn = get_conn()
    try:
        conn.execute(
            f"INSERT INTO nexus_subscription_events "
            f"(business_id, event_type, plan, amount_paise, "
            f" razorpay_order_id, razorpay_payment_id, payload_json, created_at) "
            f"VALUES ({_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()}, {_ph()})",
            (
                business_id, event_type, plan, amount_paise,
                razorpay_order_id, razorpay_payment_id,
                json.dumps(payload or {}), now_iso(),
            ),
        )
        conn.commit()
    finally:
        conn.close()


def cancel_subscription(business_id: str, reason: str = "") -> Dict[str, Any]:
    """Soft-cancel — keep history, set status='cancelled', plan reverts to
    free at current_period_end (handled by a daily reaper, not this call)."""
    conn = get_conn()
    try:
        conn.execute(
            f"UPDATE nexus_subscriptions SET status = 'cancelled', updated_at = {_ph()} "
            f"WHERE business_id = {_ph()}",
            (now_iso(), business_id),
        )
        conn.commit()
    finally:
        conn.close()
    record_event(
        business_id=business_id, event_type="cancelled",
        payload={"reason": reason},
    )
    return get_subscription(business_id)


def reap_expired() -> int:
    """Daily job: any subscription whose `current_period_end` is in the past
    AND status='active' goes to status='past_due'. After 7 days past_due,
    plan reverts to 'free'. Called from agents/background/scheduler.py."""
    now = now_iso()
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    moved_to_past_due = 0
    moved_to_free = 0

    conn = get_conn()
    try:
        # Step 1: active → past_due when current_period_end < now
        cur = conn.execute(
            f"UPDATE nexus_subscriptions SET status = 'past_due', updated_at = {_ph()} "
            f"WHERE status = 'active' AND current_period_end IS NOT NULL "
            f"AND current_period_end < {_ph()}",
            (now, now),
        )
        moved_to_past_due = getattr(cur, "rowcount", 0) or 0

        # Step 2: past_due → free when 7+ days expired
        cur = conn.execute(
            f"UPDATE nexus_subscriptions SET plan = 'free', status = 'active', "
            f"updated_at = {_ph()} "
            f"WHERE status = 'past_due' AND current_period_end < {_ph()}",
            (now, seven_days_ago),
        )
        moved_to_free = getattr(cur, "rowcount", 0) or 0

        conn.commit()
    finally:
        conn.close()

    if moved_to_past_due or moved_to_free:
        logger.info(
            f"[subscriptions reap] {moved_to_past_due} → past_due, "
            f"{moved_to_free} → free"
        )
    return moved_to_past_due + moved_to_free
