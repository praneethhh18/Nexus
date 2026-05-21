"""Plan-gated feature checks.

Single point of truth for "is this business allowed to use feature X?".
The PLANS dict in api/routers/billing.py has the limits per tier; this
module wraps the lookup so callers don't have to hand-code tier strings.

Usage:

    from api.plan_gate import require_plan, allows_feature, get_limit

    # Inside a FastAPI dependency or endpoint:
    require_plan(ctx['business_id'], 'pro')   # raises 402 if below Pro

    # Or check non-throw:
    if allows_feature(biz_id, 'privacy_bridge'):
        ...

    # Numeric quotas:
    if get_limit(biz_id, 'voice_min_mo') > used_mins:
        ...

402 Payment Required is the right HTTP status for "your plan can't access
this" — separates it from 401 (not logged in) and 403 (logged in but
forbidden by ACL). Frontend catches 402 → routes to /pricing.
"""
from __future__ import annotations

import os
from typing import Any

from fastapi import HTTPException
from loguru import logger

from api.routers.billing import PLANS, check_plan, plan_rank
from api.subscriptions import get_plan, get_subscription


def _gates_disabled() -> bool:
    """Dev / demo escape hatch — set NEXUS_DISABLE_PLAN_GATES=1 in .env to
    bypass all plan checks (Magic Workflows, voice minutes, privacy bridge,
    etc.) without faking the business's subscription record. Off by default
    so production never accidentally hands out paid features."""
    return os.getenv("NEXUS_DISABLE_PLAN_GATES", "0").strip() == "1"


def require_plan(business_id: str, required: str) -> None:
    """Raise HTTPException(402) if the business isn't on `required` or higher."""
    if _gates_disabled():
        logger.debug(f"[plan_gate] bypassed (NEXUS_DISABLE_PLAN_GATES=1) — required={required}")
        return
    current = get_plan(business_id)
    if not check_plan(current, required):
        cur_label = (PLANS.get(current) or {}).get("label", current)
        req_label = (PLANS.get(required) or {}).get("label", required)
        raise HTTPException(
            status_code=402,
            detail=(f"This feature requires the {req_label} plan or higher. "
                    f"You're currently on {cur_label}. "
                    f"Upgrade at /pricing."),
        )


def allows_feature(business_id: str, feature: str) -> bool:
    """Boolean check — does the business's plan unlock this feature flag?
    Looks up `limits.<feature>` in PLANS. Truthy values count as "yes"."""
    if _gates_disabled():
        return True
    current = get_plan(business_id)
    plan = PLANS.get(current) or {}
    limits = plan.get("limits") or {}
    return bool(limits.get(feature))


def get_limit(business_id: str, key: str, default: int = 0) -> int:
    """Fetch a numeric limit (e.g. 'voice_min_mo'). -1 means unlimited."""
    current = get_plan(business_id)
    plan = PLANS.get(current) or {}
    limits = plan.get("limits") or {}
    val = limits.get(key)
    if val is None:
        return default
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


def is_unlimited(business_id: str, key: str) -> bool:
    """Convenience: was this limit set to -1 (unlimited)?"""
    return get_limit(business_id, key, default=0) < 0


def plan_summary(business_id: str) -> dict[str, Any]:
    """Single bundle for the frontend — current plan + label + numeric
    limits + boolean feature flags + trial info. Settings/Pricing/Layout
    all read from this so they don't drift from each other."""
    sub = get_subscription(business_id)
    plan_key = sub.get("plan") or "free"
    plan = PLANS.get(plan_key) or PLANS["free"]
    return {
        "plan_key":              plan_key,
        "label":                 plan.get("label"),
        "rank":                  plan_rank(plan_key),
        "status":                sub.get("status"),
        "started_at":            sub.get("started_at"),
        "current_period_end":    sub.get("current_period_end"),
        # Trial fields — null when not on trial. Frontend uses these
        # to render the persistent "X days left" banner.
        "is_trial":              sub.get("status") == "trial",
        "trial_started_at":      sub.get("trial_started_at"),
        "trial_ends_at":         sub.get("trial_ends_at"),
        "trial_days_remaining":  sub.get("trial_days_remaining"),
        "trial_active":          sub.get("trial_active"),
        "limits":                plan.get("limits") or {},
        "features":              plan.get("features") or [],
    }
