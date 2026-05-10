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
            f"trial_started_at, trial_ends_at, updated_at "
            f"FROM nexus_subscriptions WHERE business_id = {_ph()}",
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
            "trial_started_at":      None,
            "trial_ends_at":         None,
            "last_payment_id":       None,
        }
    if hasattr(row, "keys"):
        d = dict(row)
    else:
        d = {
            "business_id":           row[0],
            "plan":                  row[1],
            "status":                row[2],
            "started_at":            row[3],
            "current_period_end":    row[4],
            "razorpay_customer_id":  row[5],
            "razorpay_subscription_id": row[6],
            "last_payment_id":       row[7],
            "trial_started_at":      row[8],
            "trial_ends_at":         row[9],
            "updated_at":            row[10],
        }
    # Convenience derived fields the frontend needs.
    if d.get("status") == "trial" and d.get("trial_ends_at"):
        try:
            ends = datetime.fromisoformat(d["trial_ends_at"])
            now = datetime.now(timezone.utc)
            d["trial_days_remaining"] = max(0, (ends.date() - now.date()).days)
            d["trial_active"] = ends > now
        except Exception:
            d["trial_days_remaining"] = None
            d["trial_active"] = False
    else:
        d["trial_days_remaining"] = None
        d["trial_active"] = False
    return d


def get_plan(business_id: str) -> str:
    """Convenience — just the plan key. Used by feature gates throughout
    the codebase: `if check_plan(get_plan(biz), 'pro'): ...`

    During trial, returns the trialled plan ('pro' typically) so feature
    gates unlock the trial experience. Trial expiry handled by reap_expired.
    """
    return (get_subscription(business_id) or {}).get("plan") or "free"


# ── Trial lifecycle ───────────────────────────────────────────────────────
TRIAL_PLAN = "pro"      # default tier the trial unlocks
TRIAL_DAYS = 14         # change here + the email copy in billing_emails.py


def start_trial(
    business_id: str,
    *,
    plan: str = TRIAL_PLAN,
    days: int = TRIAL_DAYS,
    user_id: str = "",
) -> Dict[str, Any]:
    """Grant a trial subscription. Idempotent — if the business already has
    a row (any status), this is a no-op so a second 'create_business' call
    doesn't restart the clock or reset a paid plan back to trial.

    Called from api/businesses.create_business() on first business creation.
    Safe to call eagerly — won't override a paid-active subscription.
    """
    if not business_id:
        raise ValueError("business_id required")

    existing = get_subscription(business_id)
    if existing.get("status") in ("active", "trial", "past_due", "cancelled"):
        # Don't reset whatever already exists — even cancelled/past_due
        # rows have history we want to keep.
        if existing.get("started_at") or existing.get("trial_started_at"):
            return existing

    now = datetime.now(timezone.utc)
    trial_ends = (now + timedelta(days=days)).isoformat()
    started = now.isoformat()

    conn = get_conn()
    try:
        conn.execute(
            f"INSERT INTO nexus_subscriptions "
            f"(business_id, plan, status, started_at, current_period_end, "
            f" trial_started_at, trial_ends_at, updated_at) "
            f"VALUES ({_ph()}, {_ph()}, 'trial', {_ph()}, {_ph()}, "
            f"        {_ph()}, {_ph()}, {_ph()}) "
            f"ON CONFLICT(business_id) DO NOTHING",
            (business_id, plan, started, trial_ends, started, trial_ends, now_iso()),
        )
        conn.commit()
    finally:
        conn.close()

    record_event(
        business_id=business_id,
        event_type="trial_started",
        plan=plan,
        payload={"days": days, "user_id": user_id},
    )
    logger.info(f"[subscriptions] trial started biz={business_id} plan={plan} ends={trial_ends}")

    # Welcome email — best-effort. Same fallback shape as record_payment side
    # effects: missing customer email is fine, just skip.
    try:
        from api.businesses import get_business
        from api.billing_emails import send_trial_started
        from api.routers.billing import PLANS

        biz = get_business(business_id) or {}
        customer_email = ""
        customer_name = ""
        if user_id:
            try:
                from api.auth import get_user_by_id
                u = get_user_by_id(user_id) or {}
                customer_email = u.get("email", "")
                customer_name = u.get("name", "")
            except Exception:
                pass
        if customer_email:
            send_trial_started(
                to_email=customer_email,
                customer_name=customer_name,
                business_name=biz.get("name", "your workspace"),
                plan_label=(PLANS.get(plan) or {}).get("label", plan),
                trial_days=days,
            )
    except Exception as e:
        logger.warning(f"[subscriptions] trial-started email failed: {e}")

    return get_subscription(business_id)


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

    # 2. Upsert the current-state row. Trial-aware: if there's still time
    #    left on a trial, extend the period from trial_end so the customer
    #    doesn't lose the remaining trial days they paid for.
    started_at = now_iso()
    existing = get_subscription(business_id)
    base_for_period = datetime.now(timezone.utc)
    if (existing.get("status") == "trial"
            and existing.get("trial_ends_at")):
        try:
            trial_end = datetime.fromisoformat(existing["trial_ends_at"])
            if trial_end > base_for_period:
                base_for_period = trial_end   # extend FROM trial_end, not now
        except Exception:
            pass
    plan_meta = None
    try:
        from api.routers.billing import PLANS
        plan_meta = PLANS.get(plan) or {}
    except Exception:
        plan_meta = {}
    period = (plan_meta or {}).get("period", "monthly")
    if period == "annual":
        period_end = (base_for_period + timedelta(days=365)).isoformat()
    elif period in ("one-time", "custom"):
        period_end = None
    else:
        period_end = (base_for_period + timedelta(days=30)).isoformat()

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

    # 3. Side-effects: welcome email + GST invoice + founder ping. Each
    #    wrapped in try/except so a Resend hiccup never breaks the payment
    #    flow — money + DB state are already safe at this point.
    try:
        _send_billing_side_effects(
            business_id=business_id,
            plan=plan,
            amount_paise=amount_paise,
            razorpay_order_id=razorpay_order_id,
            razorpay_payment_id=razorpay_payment_id,
            extra_payload=extra_payload,
        )
    except Exception as e:
        logger.warning(f"[subscriptions] post-payment side-effects failed: {e}")

    return get_subscription(business_id)


def _send_billing_side_effects(
    *,
    business_id: str,
    plan: str,
    amount_paise: int,
    razorpay_order_id: str,
    razorpay_payment_id: str,
    extra_payload: Optional[Dict[str, Any]],
) -> None:
    """Welcome email + GST invoice + founder ping. Best-effort — every step
    swallows its own exceptions and logs."""
    from api.routers.billing import PLANS
    from api.billing_emails import send_welcome_email, notify_founder_new_payment

    plan_meta = PLANS.get(plan) or {}
    amount_inr = amount_paise / 100.0

    # Look up customer details — graceful fallbacks if anything missing.
    try:
        from api.businesses import get_business
        biz = get_business(business_id) or {}
        business_name = biz.get("name", "your workspace")
    except Exception:
        biz = {}
        business_name = "your workspace"

    user_id = (extra_payload or {}).get("user_id") or biz.get("owner_id") or ""
    customer_email = ""
    customer_name  = ""
    customer_state = ""
    customer_gstin = ""
    if user_id:
        try:
            from api.auth import get_user_by_id
            u = get_user_by_id(user_id) or {}
            customer_email = u.get("email", "")
            customer_name  = u.get("name", "")
        except Exception:
            pass
    customer_email = customer_email or biz.get("email", "")

    # Invoice PDF — best-effort.
    invoice_bytes = None
    try:
        from report_generator.gst_invoice import render_invoice_pdf
        invoice_bytes = render_invoice_pdf(
            payment_id=razorpay_payment_id,
            order_id=razorpay_order_id,
            plan_label=plan_meta.get("label", plan),
            plan_period=plan_meta.get("period", "monthly"),
            amount_inr=amount_inr,
            customer_name=customer_name or business_name,
            customer_email=customer_email,
            customer_gstin=customer_gstin,
            customer_state_code=customer_state,
        )
    except Exception as e:
        logger.warning(f"[subscriptions] invoice render failed: {e}")

    # Welcome email to the customer.
    if customer_email:
        try:
            send_welcome_email(
                to_email=customer_email,
                customer_name=customer_name or business_name,
                business_name=business_name,
                plan_label=plan_meta.get("label", plan),
                plan_period=plan_meta.get("period", "monthly"),
                amount_inr=amount_inr,
                payment_id=razorpay_payment_id,
                order_id=razorpay_order_id,
                invoice_pdf=invoice_bytes,
                plan_features=plan_meta.get("features", []),
            )
        except Exception as e:
            logger.warning(f"[subscriptions] welcome email failed: {e}")

    # Founder ping (you).
    try:
        notify_founder_new_payment(
            business_name=business_name,
            business_id=business_id,
            customer_name=customer_name or "—",
            customer_email=customer_email or "—",
            plan_label=plan_meta.get("label", plan),
            amount_inr=amount_inr,
            payment_id=razorpay_payment_id,
        )
    except Exception as e:
        logger.warning(f"[subscriptions] founder ping failed: {e}")


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
    """Daily job: three transitions, ordered for safety.

    1. Trial expiry: status='trial' AND trial_ends_at < now → plan='free',
       status='active'. Customer keeps their data; only the Pro features
       lock. The trial_started_at/trial_ends_at columns stay as audit.
    2. Active expiry: status='active' AND current_period_end < now →
       status='past_due'. Renewal-failure email sequence handles recovery.
    3. Past-due expiry: status='past_due' for 7+ days → plan='free',
       status='active'. The customer effectively cancelled.
    """
    now = now_iso()
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    expired_trials = 0
    moved_to_past_due = 0
    moved_to_free = 0

    conn = get_conn()
    try:
        # Step 0: trial → free when trial_ends_at is past
        cur = conn.execute(
            f"UPDATE nexus_subscriptions SET plan = 'free', status = 'active', "
            f"updated_at = {_ph()} "
            f"WHERE status = 'trial' AND trial_ends_at IS NOT NULL "
            f"AND trial_ends_at < {_ph()}",
            (now, now),
        )
        expired_trials = getattr(cur, "rowcount", 0) or 0

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

    total = expired_trials + moved_to_past_due + moved_to_free
    if total:
        logger.info(
            f"[subscriptions reap] {expired_trials} trial→free, "
            f"{moved_to_past_due} active→past_due, "
            f"{moved_to_free} past_due→free"
        )
    return total
