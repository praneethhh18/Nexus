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

# Plan catalogue — single source of truth. Frontend (in-app /pricing AND
# the public landing page) reads from /api/billing/plans so the price the
# customer sees on marketing pages matches the price Razorpay actually
# charges. Drift here = trust killer. Update everywhere or nowhere.
#
# Tier ladder (low → high). `rank` enforces upgrade-only flows in the UI
# and `check_plan(required)` permission helper.
#
# Pricing principles:
#   - Anchor against Zoho CRM Standard (₹1,200/seat) and HubSpot Starter
#     (₹2,500/seat) — the SMB Indian buyer's mental anchor.
#   - Pro is the "this is the obvious one" tier — most features unlocked.
#   - Privacy is the moat — Privacy Bridge is unique to NexusAgent.
#   - Self-hosted via separate sales conversation, not Razorpay.
PLANS = {
    "free": {
        "label":      "Free",
        "price_inr":  0,
        "period":     "forever",
        "rank":       0,
        "limits": {
            "users":         1,
            "agents":        2,        # pick any 2 of the 8
            "documents":     100,
            "whatsapp_mo":   0,
            "voice_min_mo":  0,
            "cloud_llm":     False,
            "privacy_bridge": False,
        },
        "features": [
            "1 user",
            "2 AI agents (you pick which)",
            "100 documents in RAG",
            "Local LLM only (no cloud)",
            "Community support (GitHub issues)",
        ],
        "purchasable": False,  # not via Razorpay
    },
    "starter": {
        "label":      "Starter",
        "price_inr":  1499,
        "period":     "monthly",
        "rank":       1,
        "limits": {
            "users":         2,
            "agents":        5,
            "documents":     500,
            "whatsapp_mo":   100,
            "voice_min_mo":  30,
            "cloud_llm":     False,
            "privacy_bridge": False,
        },
        "features": [
            "2 users",
            "5 AI agents (you pick which)",
            "500 documents in RAG",
            "100 WhatsApp messages/month",
            "30 voice minutes/month (Vox)",
            "Local LLM only",
            "Email support",
        ],
        "purchasable": True,
    },
    "pro": {
        "label":      "Pro",
        "price_inr":  5999,                 # ⭐ flagship — anchor against HubSpot Starter
        "period":     "monthly",
        "rank":       2,
        "popular":    True,
        "limits": {
            "users":         5,
            "agents":        8,             # all of them
            "documents":     2000,
            "whatsapp_mo":   500,
            "voice_min_mo":  100,
            "cloud_llm":     True,
            "privacy_bridge": False,
        },
        "features": [
            "Up to 5 users",
            "All 8 AI agents",
            "2,000 documents in RAG",
            "500 WhatsApp messages/month",
            "100 voice minutes/month",
            "Cloud LLM enabled (Claude / Bedrock / NVIDIA)",
            "AI proposals + Calendar + Email integration",
            "Email support",
        ],
        "purchasable": True,
    },
    "privacy": {
        "label":      "Privacy",
        "price_inr":  14999,                # privacy bridge moat — premium pricing
        "period":     "monthly",
        "rank":       3,
        "limits": {
            "users":         10,
            "agents":        8,
            "documents":     10000,
            "whatsapp_mo":   2000,
            "voice_min_mo":  300,
            "cloud_llm":     True,
            "privacy_bridge": True,
        },
        "features": [
            "Up to 10 users",
            "All 8 AI agents",
            "10,000 documents in RAG",
            "2,000 WhatsApp messages/month",
            "300 voice minutes/month",
            "Privacy Bridge — sensitive prompts run on YOUR laptop",
            "Cloud LLM with PII redaction",
            "Priority support (24h response)",
        ],
        "purchasable": True,
    },
    "self_hosted": {
        "label":      "Self-hosted",
        "price_inr":  499000,                # ₹4.99 L one-time license
        "period":     "one-time",
        "rank":       4,
        # Optional annual support contract — sold separately, this is the
        # industry standard 15% of license to keep updates flowing forever.
        "annual_support_inr": 74999,
        "limits": {
            "users":         -1,
            "agents":        8,
            "documents":     -1,
            "whatsapp_mo":   -1,
            "voice_min_mo":  -1,
            "cloud_llm":     True,
            "privacy_bridge": True,
        },
        "features": [
            "Unlimited users on your own server",
            "Docker + Helm deploy",
            "Full source code access",
            "12 months of updates included",
            "Bring-your-own API keys (no usage fees from us)",
            "Setup support via email",
            "Optional annual support: ₹74,999/year (priority + new versions)",
        ],
        "purchasable": False,  # license sale, mailto path — quote per buyer
    },
}


def plan_rank(plan_key: str) -> int:
    """Numeric rank for upgrade comparisons. Unknown plan → 0 (treat as free)."""
    return PLANS.get(plan_key, {}).get("rank", 0)


def check_plan(business_plan: str, required: str) -> bool:
    """True if `business_plan` meets or exceeds `required`. Used by feature
    gates: `if not check_plan(biz.plan, 'pro'): raise 402`."""
    return plan_rank(business_plan) >= plan_rank(required)


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


# ── Current subscription state (for the in-app UI) ────────────────────────
@router.get("/api/billing/subscription")
def my_subscription(ctx: dict = Depends(get_current_context)):
    """Return the current business's plan + limits + features. The Settings
    and Pricing pages call this to render the 'Your plan' panel and to
    decide which CTA each tier shows ('Upgrade' vs 'You're on this plan')."""
    from api.plan_gate import plan_summary
    return plan_summary(ctx["business_id"])


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

    # Signature verified — payment is real. Persist the subscription state
    # change. record_payment() is idempotent on payment_id so a refresh that
    # double-fires verify-payment won't double-extend the period.
    plan_for_payment = body.plan or "pro"  # default to pro if client didn't echo it
    plan_meta = PLANS.get(plan_for_payment) or {}
    amount_paise = (plan_meta.get("price_inr") or 0) * 100

    try:
        from api import subscriptions as _subs
        sub = _subs.record_payment(
            business_id=ctx["business_id"],
            plan=plan_for_payment,
            amount_paise=amount_paise,
            razorpay_order_id=body.razorpay_order_id,
            razorpay_payment_id=body.razorpay_payment_id,
            event_type="payment_verified",
            extra_payload={"user_id": ctx["user"]["id"]},
        )
    except Exception as e:
        # Verification succeeded — the payment IS valid. If our DB write
        # bombs, log loudly but still return success so the customer doesn't
        # think they paid for nothing. The audit log will catch the drift.
        logger.exception(f"[billing] subscription persist failed: {e}")
        sub = {"plan": plan_for_payment, "status": "active"}

    logger.success(
        f"[billing] payment verified payment={body.razorpay_payment_id} "
        f"order={body.razorpay_order_id} plan={plan_for_payment} biz={ctx['business_id']}"
    )

    return {
        "ok":          True,
        "verified":    True,
        "order_id":    body.razorpay_order_id,
        "payment_id":  body.razorpay_payment_id,
        "plan":        plan_for_payment,
        "subscription": sub,
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
    payload = event.get("payload", {}) or {}
    logger.info(f"[billing] webhook event={event_type}")

    # Razorpay's webhook payload schema:
    #   payment.captured / payment.failed:
    #       payload.payment.entity = {id, order_id, amount, status, notes:{business_id, plan}}
    #   refund.created:
    #       payload.refund.entity  = {id, payment_id, amount}
    #       payload.payment.entity = {id, ...}  (the original payment being refunded)
    from api import subscriptions as _subs

    payment_entity = (payload.get("payment", {}) or {}).get("entity", {}) or {}
    refund_entity  = (payload.get("refund",  {}) or {}).get("entity",  {}) or {}
    notes = payment_entity.get("notes", {}) or {}
    biz_id = notes.get("business_id") or ""
    plan   = notes.get("plan") or "pro"

    try:
        if event_type == "payment.captured" and biz_id:
            # Same effect as a successful verify-payment — record_payment is
            # idempotent on payment_id so a webhook arriving after a fast
            # /verify-payment call won't double-extend.
            _subs.record_payment(
                business_id=biz_id,
                plan=plan,
                amount_paise=int(payment_entity.get("amount", 0)),
                razorpay_order_id=payment_entity.get("order_id", ""),
                razorpay_payment_id=payment_entity.get("id", ""),
                event_type="payment_captured",
                extra_payload={"webhook": True},
            )
        elif event_type == "payment.failed" and biz_id:
            _subs.record_event(
                business_id=biz_id,
                event_type="payment_failed",
                plan=plan,
                amount_paise=int(payment_entity.get("amount", 0)),
                razorpay_order_id=payment_entity.get("order_id", ""),
                razorpay_payment_id=payment_entity.get("id", ""),
                payload={"reason": payment_entity.get("error_description", ""),
                         "webhook": True},
            )
        elif event_type == "refund.created" and biz_id:
            # Refund — log only. Manual review decides whether to revert
            # the plan or keep it; we don't auto-downgrade on a refund
            # because some refunds are partial / dispute-driven.
            _subs.record_event(
                business_id=biz_id,
                event_type="refund_created",
                plan=plan,
                amount_paise=int(refund_entity.get("amount", 0)),
                razorpay_payment_id=refund_entity.get("payment_id", ""),
                payload={"refund_id": refund_entity.get("id", ""), "webhook": True},
            )
        else:
            # Subscriptions, orders, etc. — log only for now.
            logger.debug(f"[billing] webhook unhandled event_type={event_type}")
    except Exception as e:
        # Webhook handler failures must NEVER 500 — Razorpay retries failed
        # webhooks and we'd loop forever. Log and ack-200.
        logger.exception(f"[billing] webhook handler error: {e}")

    return {"ok": True, "event": event_type}
