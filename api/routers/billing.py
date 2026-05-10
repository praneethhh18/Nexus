"""Razorpay billing — order creation + payment signature verification.

Flow:
    1. Customer clicks "Subscribe" on the pricing page.
    2. Frontend POSTs /api/billing/create-order with {amount_paise, plan, period}.
    3. We hit Razorpay's POST /v1/orders with the same fields and return the
       order_id back to the frontend.
    4. Frontend opens Razorpay Checkout modal with that order_id.
    5. After the user pays, Razorpay returns three values to the frontend:
       razorpay_payment_id, razorpay_order_id, razorpay_signature.
    6. Frontend POSTs them to /api/billing/verify-payment.
    7. We recompute the HMAC-SHA256 signature server-side and compare.
       Match → mark the business's subscription active. Mismatch → 400, no DB
       changes (we never trust frontend-supplied "I paid").

Why we don't import the razorpay SDK at top-level:
    The SDK is optional in dev (when RAZORPAY_KEY_ID isn't set the routes
    return clean 503s instead of crashing on missing dep). Lazy-import keeps
    boot fast for devs who haven't run `pip install razorpay` yet.
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from loguru import logger
from pydantic import BaseModel, Field

from api.auth import get_current_context

router = APIRouter(tags=["billing"])

# Plan catalogue — single source of truth for "what does each tier cost?".
# Frontend reads /api/billing/plans to populate the pricing page so prices
# never drift between the marketing site and the actual checkout amount.
PLANS = {
    "starter": {
        "label":      "Starter",
        "price_inr":  999,
        "period":     "monthly",
        "features":   ["Web CRM", "8 AI agents", "100 WhatsApp/mo", "30 voice mins/mo"],
    },
    "pro": {
        "label":      "Pro",
        "price_inr":  2499,
        "period":     "monthly",
        "features":   ["Everything in Starter", "500 WhatsApp", "200 voice mins",
                       "AI proposals", "Calendar + Email integration"],
    },
    "privacy": {
        "label":      "Privacy",
        "price_inr":  5999,
        "period":     "monthly",
        "features":   ["Everything in Pro", "Privacy Bridge (data on your laptop)",
                       "2,000 WhatsApp", "500 voice mins", "Priority support"],
    },
}


def _client():
    """Build a Razorpay client. Raises 503 if keys aren't configured so the
    error is actionable instead of an opaque AttributeError downstream."""
    key_id = (os.getenv("RAZORPAY_KEY_ID") or "").strip()
    key_secret = (os.getenv("RAZORPAY_KEY_SECRET") or "").strip()
    if not key_id or not key_secret:
        raise HTTPException(
            503,
            "Razorpay not configured. Set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET "
            "in your .env (get test keys from dashboard.razorpay.com).",
        )
    try:
        import razorpay
    except ImportError:
        raise HTTPException(
            503,
            "razorpay SDK not installed. Run: pip install razorpay",
        )
    return razorpay.Client(auth=(key_id, key_secret))


# ── Request models ────────────────────────────────────────────────────────
class CreateOrderRequest(BaseModel):
    plan: Optional[str] = Field(None, description="Plan key from /plans")
    amount_paise: Optional[int] = Field(None, ge=100,
        description="Override amount in paise (≥100). Used for one-off charges.")
    currency: str = Field("INR", min_length=3, max_length=3)
    notes: dict = Field(default_factory=dict, description="Free-form metadata")


class VerifyPaymentRequest(BaseModel):
    razorpay_order_id:   str = Field(..., min_length=1)
    razorpay_payment_id: str = Field(..., min_length=1)
    razorpay_signature:  str = Field(..., min_length=1)
    plan:                Optional[str] = None


# ── Public catalogue ──────────────────────────────────────────────────────
@router.get("/api/billing/plans")
def list_plans():
    """Return the plan catalogue. Public — no auth needed (used by both the
    marketing landing page and the in-app pricing page)."""
    return {
        "plans":      PLANS,
        "currency":   "INR",
        "key_id":     os.getenv("RAZORPAY_KEY_ID", ""),  # public, safe to expose
    }


# ── Order creation ────────────────────────────────────────────────────────
@router.post("/api/billing/create-order")
def create_order(
    body: CreateOrderRequest,
    ctx: dict = Depends(get_current_context),
):
    """Mint a Razorpay order. The amount comes either from the named plan or
    from an explicit `amount_paise` override. We DON'T trust the client to
    send the price — for plan-based orders we look it up server-side."""
    if body.plan:
        plan = PLANS.get(body.plan)
        if not plan:
            raise HTTPException(400, f"unknown plan: {body.plan!r}")
        amount_paise = plan["price_inr"] * 100
    elif body.amount_paise:
        amount_paise = body.amount_paise
    else:
        raise HTTPException(400, "must provide either `plan` or `amount_paise`")

    if amount_paise < 100:
        raise HTTPException(400, "amount must be at least 100 paise (₹1)")

    # receipt = short human-readable id, helpful in Razorpay's dashboard later.
    # 40 char limit per Razorpay docs.
    receipt = f"nx_{ctx['business_id'][:8]}_{int(time.time())}_{secrets.token_hex(3)}"[:40]

    notes = {
        "business_id": ctx["business_id"],
        "user_id":     ctx["user"]["id"],
        "plan":        body.plan or "custom",
        **(body.notes or {}),
    }

    client = _client()
    try:
        order = client.order.create({
            "amount":         amount_paise,
            "currency":       body.currency,
            "receipt":        receipt,
            "notes":          notes,
            "payment_capture": 1,  # auto-capture on successful auth
        })
    except Exception as e:
        logger.exception(f"[billing] Razorpay order.create failed: {e}")
        # 502 — upstream error. Distinguishes from 500 (our bug).
        raise HTTPException(502, f"Razorpay order creation failed: {e}")

    logger.info(f"[billing] order created {order.get('id')} amount={amount_paise} biz={ctx['business_id']}")
    return {
        "order_id": order["id"],
        "amount":   order["amount"],
        "currency": order["currency"],
        "receipt":  order["receipt"],
        "key_id":   os.getenv("RAZORPAY_KEY_ID", ""),
    }


# ── Signature verification ────────────────────────────────────────────────
@router.post("/api/billing/verify-payment")
def verify_payment(
    body: VerifyPaymentRequest,
    ctx: dict = Depends(get_current_context),
):
    """Confirm Razorpay actually signed this payment. Only after a valid
    signature do we treat the payment as real and (eventually) update the
    business's subscription state.

    The signature is HMAC-SHA256(order_id + '|' + payment_id, KEY_SECRET).
    Constant-time compare so an attacker can't time-attack the secret.
    """
    key_secret = (os.getenv("RAZORPAY_KEY_SECRET") or "").strip()
    if not key_secret:
        raise HTTPException(503, "Razorpay not configured")

    payload = f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode("utf-8")
    expected = hmac.new(
        key_secret.encode("utf-8"),
        payload,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, body.razorpay_signature):
        logger.warning(
            f"[billing] signature MISMATCH order={body.razorpay_order_id} "
            f"payment={body.razorpay_payment_id} biz={ctx['business_id']}"
        )
        raise HTTPException(400, "invalid payment signature")

    # Signature verified — payment is real. Hand off to subscription state
    # update. For now we just log; wire this to a subscriptions table when the
    # plans/seats schema lands.
    logger.success(
        f"[billing] payment verified payment={body.razorpay_payment_id} "
        f"order={body.razorpay_order_id} plan={body.plan} biz={ctx['business_id']}"
    )

    return {
        "ok":          True,
        "verified":    True,
        "order_id":    body.razorpay_order_id,
        "payment_id":  body.razorpay_payment_id,
        "plan":        body.plan,
        # Frontend uses this to redirect to a success page.
        "next":        "/settings?billing=success",
    }


# ── Webhook (Razorpay → us) ───────────────────────────────────────────────
@router.post("/api/billing/webhook")
async def razorpay_webhook(request: Request):
    """Razorpay calls this on payment events (captured / failed / refunded).
    We verify the X-Razorpay-Signature header and ignore unsigned hits.

    Configure in Razorpay Dashboard → Settings → Webhooks:
      URL:   https://app.nexusagent.in/api/billing/webhook
      Secret: any random string (set RAZORPAY_WEBHOOK_SECRET to match)
      Events: payment.captured, payment.failed, refund.created
    """
    webhook_secret = (os.getenv("RAZORPAY_WEBHOOK_SECRET") or "").strip()
    if not webhook_secret:
        # No secret configured — accept the request but log it. Lets you set
        # up webhooks before configuring the secret without losing events.
        logger.warning("[billing] webhook hit without RAZORPAY_WEBHOOK_SECRET set")
        return {"ok": True, "verified": False}

    raw_body = await request.body()
    signature = request.headers.get("X-Razorpay-Signature", "")
    expected = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        logger.warning("[billing] webhook signature mismatch")
        raise HTTPException(400, "invalid webhook signature")

    try:
        import json as _json
        event = _json.loads(raw_body.decode("utf-8"))
    except Exception:
        raise HTTPException(400, "invalid JSON body")

    event_type = event.get("event", "?")
    logger.info(f"[billing] webhook event={event_type}")
    # Future: dispatch to subscription state updates by event_type.
    return {"ok": True, "event": event_type}
