"""Transactional emails sent in response to billing events.

Emails:
  send_welcome_email     — fires from subscriptions.record_payment()
                            on a verified payment. Includes the GST invoice
                            PDF as an attachment + plain-text receipt.
  send_renewal_reminder  — fires from the daily scheduler 3 days and 1 day
                            before current_period_end.
  send_renewal_failed    — fires when an auto-renewal Razorpay attempt
                            fails (webhook payment.failed for a renewal).
  notify_founder         — Slack / WhatsApp / email ping to YOU on every
                            new paid customer. Configurable channel.

Failures here MUST NEVER block the payment flow. Every send is wrapped in
try/except — log loud, return False, never raise.
"""
from __future__ import annotations

import os
from datetime import datetime
from typing import Optional

from loguru import logger

from api.email_provider import send_email


# ── Helpers ───────────────────────────────────────────────────────────────
def _app_url() -> str:
    return (os.getenv("APP_BASE_URL") or "https://app.nexusagent.in").rstrip("/")


def _support_email() -> str:
    return os.getenv("SUPPORT_EMAIL") or os.getenv("EMAIL_FROM_ADDRESS_ONLY") or "hi@nexusagent.in"


def _founder_email() -> str:
    """Address that gets the "💰 new customer" ping. Defaults to the same
    sender as transactional mail; override per-deployment."""
    return (os.getenv("FOUNDER_NOTIFY_EMAIL") or "").strip() or _support_email()


def _format_inr(amount_inr: float) -> str:
    return f"₹{amount_inr:,.2f}"


# ── Welcome + receipt email ───────────────────────────────────────────────
def send_welcome_email(
    *,
    to_email: str,
    customer_name: str,
    business_name: str,
    plan_label: str,
    plan_period: str,
    amount_inr: float,
    payment_id: str,
    order_id: str,
    invoice_pdf: Optional[bytes] = None,
    plan_features: Optional[list] = None,
) -> bool:
    """Welcome + receipt + GST invoice. Returns True on success.

    `invoice_pdf` is the bytes returned by report_generator.gst_invoice —
    attached as `invoice-NX-YYYYMM-XXXXX.pdf` if provided.
    """
    if not to_email:
        logger.warning("[billing-email] welcome skipped — no to_email")
        return False

    features_block = ""
    if plan_features:
        features_block = "\n\nWhat's now unlocked for you:\n" + "\n".join(
            f"  ✓ {f}" for f in plan_features[:8]   # cap to 8 to keep email tight
        )

    subject = f"Welcome to NexusAgent {plan_label} — payment received"

    body = (
        f"Hi {customer_name or 'there'},\n\n"
        f"Thanks for upgrading {business_name or 'your workspace'} to "
        f"NexusAgent {plan_label}. Your payment of {_format_inr(amount_inr)} "
        f"({plan_period}) has been received and your account is active.\n"
        f"{features_block}\n\n"
        f"Receipt details:\n"
        f"  • Payment ID: {payment_id}\n"
        f"  • Order ID:   {order_id}\n"
        f"  • Date:       {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}\n"
        f"  • Amount:     {_format_inr(amount_inr)} (incl. taxes)\n\n"
        f"A GST invoice is attached to this email for your records.\n\n"
        f"Get started → {_app_url()}/dashboard?welcome={plan_label.lower()}\n\n"
        f"If anything's not working or you have questions, just reply to "
        f"this email — we read every one.\n\n"
        f"Welcome aboard.\n"
        f"— Team NexusAgent"
    )

    html = (
        f"<div style=\"font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',"
        f"system-ui,sans-serif;color:#0F172A;max-width:560px;margin:0 auto\">"
        f"<div style=\"background:linear-gradient(135deg,#6366F1,#8B5CF6);"
        f"padding:32px 24px;border-radius:12px 12px 0 0;color:#fff\">"
        f"<h1 style=\"margin:0;font-size:24px\">Welcome to {plan_label}</h1>"
        f"<p style=\"margin:6px 0 0;opacity:0.9\">Payment received — you're all set.</p>"
        f"</div>"
        f"<div style=\"padding:24px;background:#F8FAFC;border:1px solid #E2E8F0;border-top:none\">"
        f"<p>Hi {customer_name or 'there'},</p>"
        f"<p>Thanks for upgrading <b>{business_name or 'your workspace'}</b> to "
        f"NexusAgent {plan_label}. Your payment of "
        f"<b>{_format_inr(amount_inr)}</b> ({plan_period}) is confirmed.</p>"
        f"{('<h3 style=\"margin-top:24px\">Now unlocked for you</h3><ul>'+''.join(f'<li>{f}</li>' for f in (plan_features or [])[:8])+'</ul>') if plan_features else ''}"
        f"<table style=\"width:100%;margin:24px 0;border-collapse:collapse;font-size:13px\">"
        f"<tr><td style=\"padding:6px 0;color:#64748B\">Payment ID</td>"
        f"<td style=\"padding:6px 0;text-align:right;font-family:ui-monospace,monospace\">{payment_id}</td></tr>"
        f"<tr><td style=\"padding:6px 0;color:#64748B\">Order ID</td>"
        f"<td style=\"padding:6px 0;text-align:right;font-family:ui-monospace,monospace\">{order_id}</td></tr>"
        f"<tr><td style=\"padding:6px 0;color:#64748B\">Date</td>"
        f"<td style=\"padding:6px 0;text-align:right\">{datetime.now().strftime('%d %b %Y, %I:%M %p IST')}</td></tr>"
        f"<tr><td style=\"padding:6px 0;color:#64748B;font-weight:600\">Amount paid</td>"
        f"<td style=\"padding:6px 0;text-align:right;font-weight:600;font-size:15px\">{_format_inr(amount_inr)}</td></tr>"
        f"</table>"
        f"<p style=\"font-size:13px;color:#64748B\">A GST invoice is attached for your records.</p>"
        f"<a href=\"{_app_url()}/dashboard?welcome={plan_label.lower()}\" "
        f"style=\"display:inline-block;background:#6366F1;color:#fff;text-decoration:none;"
        f"padding:12px 22px;border-radius:8px;font-weight:600;margin-top:8px\">"
        f"Get started →</a>"
        f"<p style=\"font-size:12px;color:#94A3B8;margin-top:32px\">"
        f"Questions? Just reply — every email reaches us.<br/>"
        f"Team NexusAgent"
        f"</p>"
        f"</div></div>"
    )

    attachments = []
    if invoice_pdf:
        invoice_filename = (
            f"NexusAgent-Invoice-{datetime.now().strftime('%Y%m')}-"
            f"{(payment_id or 'X')[-8:].upper()}.pdf"
        )
        attachments.append({"filename": invoice_filename, "content": invoice_pdf})

    try:
        send_email(
            to=to_email,
            subject=subject,
            body=body,
            html_body=html,
            attachments=attachments or None,
            reply_to=_support_email(),
        )
        logger.success(f"[billing-email] welcome sent to {to_email} ({plan_label})")
        return True
    except Exception as e:
        logger.exception(f"[billing-email] welcome failed for {to_email}: {e}")
        return False


# ── Founder ping ──────────────────────────────────────────────────────────
def notify_founder_new_payment(
    *,
    business_name: str,
    business_id: str,
    customer_name: str,
    customer_email: str,
    plan_label: str,
    amount_inr: float,
    payment_id: str,
) -> bool:
    """Email YOU when a customer pays. Set FOUNDER_NOTIFY_EMAIL in .env to
    route to a dedicated address; otherwise goes to EMAIL_FROM."""
    addr = _founder_email()
    if not addr:
        logger.warning("[billing-email] founder ping skipped — no FOUNDER_NOTIFY_EMAIL")
        return False

    subject = f"💰 NexusAgent: {business_name} paid {_format_inr(amount_inr)} ({plan_label})"
    body = (
        f"New paid customer.\n\n"
        f"Business:  {business_name}\n"
        f"Plan:      {plan_label}\n"
        f"Amount:    {_format_inr(amount_inr)}\n"
        f"Customer:  {customer_name} <{customer_email}>\n"
        f"Payment:   {payment_id}\n"
        f"Biz ID:    {business_id}\n"
        f"Time:      {datetime.now().strftime('%d %b %Y, %I:%M %p IST')}\n\n"
        f"View dashboard: {_app_url()}/admin/metrics\n"
    )
    try:
        send_email(to=addr, subject=subject, body=body, reply_to=customer_email or None)
        logger.success(f"[billing-email] founder pinged at {addr}")
        return True
    except Exception as e:
        # Founder pings should NEVER block customer flow — log only.
        logger.warning(f"[billing-email] founder ping failed: {e}")
        return False


# ── Renewal reminders ─────────────────────────────────────────────────────
def send_renewal_reminder(
    *,
    to_email: str,
    customer_name: str,
    business_name: str,
    plan_label: str,
    amount_inr: float,
    days_until_renewal: int,
) -> bool:
    """3-day and 1-day reminders before the current period ends. Same body
    template, copy varies by `days_until_renewal`."""
    if not to_email:
        return False
    when = "tomorrow" if days_until_renewal <= 1 else f"in {days_until_renewal} days"
    subject = f"Your NexusAgent {plan_label} plan renews {when}"
    body = (
        f"Hi {customer_name or 'there'},\n\n"
        f"This is a heads-up that your NexusAgent {plan_label} subscription "
        f"({business_name or 'your workspace'}) renews {when} for "
        f"{_format_inr(amount_inr)}.\n\n"
        f"Nothing to do if you want to keep going — Razorpay will charge the "
        f"same payment method.\n\n"
        f"To change plan, update your card, or cancel:\n"
        f"  → {_app_url()}/pricing\n\n"
        f"Questions? Reply to this email.\n\n"
        f"— Team NexusAgent"
    )
    try:
        send_email(to=to_email, subject=subject, body=body, reply_to=_support_email())
        return True
    except Exception as e:
        logger.warning(f"[billing-email] reminder failed for {to_email}: {e}")
        return False


# ── Trial lifecycle emails ────────────────────────────────────────────────
def send_trial_started(
    *,
    to_email: str,
    customer_name: str,
    business_name: str,
    plan_label: str = "Pro",
    trial_days: int = 14,
) -> bool:
    """Welcome email on signup — "your trial is live, here's how to start"."""
    if not to_email:
        return False
    subject = f"Welcome to NexusAgent — your {trial_days}-day {plan_label} trial is live"
    body = (
        f"Hi {customer_name or 'there'},\n\n"
        f"Welcome to NexusAgent. We've set up {business_name or 'your workspace'} "
        f"with a {trial_days}-day {plan_label} trial — no card required.\n\n"
        f"You have full access to:\n"
        f"  ✓ All 8 AI agents (CRM, Vox voice, WhatsApp, email triage, briefing, etc.)\n"
        f"  ✓ Cloud LLM (Claude / Bedrock)\n"
        f"  ✓ Calendar + email integration\n"
        f"  ✓ AI proposals + business card OCR\n\n"
        f"First-day suggestions:\n"
        f"  1. Add your first contact in CRM\n"
        f"  2. Try the magic search: ask \"who are my top 5 deals?\"\n"
        f"  3. Connect your calendar so meetings auto-prep\n\n"
        f"Get started → {_app_url()}/\n\n"
        f"You'll see a small banner showing days remaining at the top of the app. "
        f"You can subscribe anytime from /pricing — paying during the trial keeps "
        f"all your trial days, you don't lose them.\n\n"
        f"Stuck? Reply to this email — we'll help.\n\n"
        f"— Team NexusAgent"
    )
    try:
        send_email(to=to_email, subject=subject, body=body, reply_to=_support_email())
        logger.success(f"[billing-email] trial-started sent to {to_email}")
        return True
    except Exception as e:
        logger.warning(f"[billing-email] trial-started failed: {e}")
        return False


def send_trial_reminder(
    *,
    to_email: str,
    customer_name: str,
    business_name: str,
    plan_label: str,
    days_remaining: int,
) -> bool:
    """Sent on trial day 7 (halfway), day 11 (3 left), day 13 (1 left).
    Copy varies by `days_remaining`."""
    if not to_email:
        return False

    if days_remaining >= 7:
        # Halfway-point nudge — encourage exploration before pushing for upgrade.
        subject = f"You're halfway through your NexusAgent {plan_label} trial"
        body = (
            f"Hi {customer_name or 'there'},\n\n"
            f"Quick check-in — {business_name or 'your workspace'} has 7 days left "
            f"on the {plan_label} trial.\n\n"
            f"Some features people often miss in week 1:\n"
            f"  • The magic search (top of any page) — ask anything in plain English\n"
            f"  • Vox voice agent — make calls and the AI does the talking\n"
            f"  • Privacy Bridge (Privacy tier) — sensitive prompts on YOUR laptop\n\n"
            f"Open NexusAgent → {_app_url()}/\n\n"
            f"Anything blocking? Just reply.\n\n"
            f"— Team NexusAgent"
        )
    elif days_remaining >= 3:
        subject = f"3 days left on your NexusAgent {plan_label} trial"
        body = (
            f"Hi {customer_name or 'there'},\n\n"
            f"Your {plan_label} trial for {business_name or 'your workspace'} "
            f"ends in 3 days.\n\n"
            f"If you'd like to keep going, you can subscribe at:\n"
            f"  → {_app_url()}/pricing\n\n"
            f"You won't lose your trial days — paying now extends from your "
            f"trial-end date, not from today.\n\n"
            f"If NexusAgent isn't the right fit, no worries — your account "
            f"drops to the Free tier when the trial ends, all your data stays.\n\n"
            f"Questions? Reply to this email.\n\n"
            f"— Team NexusAgent"
        )
    else:
        # Day 13 — 1 day left.
        subject = f"Last day of your NexusAgent {plan_label} trial"
        body = (
            f"Hi {customer_name or 'there'},\n\n"
            f"Your {plan_label} trial ends tomorrow. After that, "
            f"{business_name or 'your workspace'} drops to the Free tier "
            f"(your data stays — Pro features just lock).\n\n"
            f"To keep Pro:\n"
            f"  → {_app_url()}/pricing  (UPI, card, or netbanking via Razorpay)\n\n"
            f"Need more time? Reply to this email and we'll extend your trial — "
            f"we'd rather you stick around.\n\n"
            f"— Team NexusAgent"
        )

    try:
        send_email(to=to_email, subject=subject, body=body, reply_to=_support_email())
        return True
    except Exception as e:
        logger.warning(f"[billing-email] trial-reminder ({days_remaining}d) failed: {e}")
        return False


def send_trial_expired(
    *,
    to_email: str,
    customer_name: str,
    business_name: str,
    plan_label: str = "Pro",
) -> bool:
    """Day 14 — trial ended. Friendly "you've moved to Free" email."""
    if not to_email:
        return False
    subject = f"Your NexusAgent {plan_label} trial has ended"
    body = (
        f"Hi {customer_name or 'there'},\n\n"
        f"Your 14-day {plan_label} trial for {business_name or 'your workspace'} "
        f"has ended. We've moved you to the Free tier.\n\n"
        f"What changes:\n"
        f"  • All your data stays exactly where it is — nothing deleted\n"
        f"  • Free tier limits: 1 user, 2 AI agents, 100 documents, local LLM only\n"
        f"  • Pro features lock until you subscribe\n\n"
        f"Want to keep Pro?\n"
        f"  → {_app_url()}/pricing  (subscribe in 30 seconds with UPI)\n\n"
        f"Or if NexusAgent wasn't right for you, no hard feelings — you can keep "
        f"using the Free tier as long as you like, or export your data anytime "
        f"from Settings.\n\n"
        f"Was something missing? We'd love a 1-line reply telling us what.\n\n"
        f"— Team NexusAgent"
    )
    try:
        send_email(to=to_email, subject=subject, body=body, reply_to=_support_email())
        return True
    except Exception as e:
        logger.warning(f"[billing-email] trial-expired failed: {e}")
        return False


# ── Renewal failure / grace period ────────────────────────────────────────
def send_renewal_failed(
    *,
    to_email: str,
    customer_name: str,
    business_name: str,
    plan_label: str,
    amount_inr: float,
    grace_days: int = 3,
    attempt: int = 1,
) -> bool:
    """Sent on Razorpay payment.failed for a renewal attempt. Three rounds
    over `grace_days` before downgrading."""
    if not to_email:
        return False
    if attempt == 1:
        subject = f"Heads-up — payment didn't go through for NexusAgent {plan_label}"
        urgency = "We'll retry automatically over the next few days."
    elif attempt == 2:
        subject = f"NexusAgent {plan_label} — payment still pending"
        urgency = "Please update your card to avoid losing Pro features."
    else:
        subject = f"Last chance — NexusAgent {plan_label} ends in {grace_days} day(s)"
        urgency = (
            f"Your account will move to Free in {grace_days} day(s) if payment "
            f"doesn't go through. Your data stays — features re-lock."
        )
    body = (
        f"Hi {customer_name or 'there'},\n\n"
        f"We tried to renew your NexusAgent {plan_label} subscription "
        f"({business_name or 'your workspace'}) for {_format_inr(amount_inr)} "
        f"but the payment didn't complete.\n\n"
        f"{urgency}\n\n"
        f"Update your payment method:\n"
        f"  → {_app_url()}/pricing\n\n"
        f"Common reasons for declined cards on Indian banks:\n"
        f"  • International transactions disabled (toggle in your bank app)\n"
        f"  • Insufficient limit\n"
        f"  • Card expired\n\n"
        f"Reply to this email if you need help.\n\n"
        f"— Team NexusAgent"
    )
    try:
        send_email(to=to_email, subject=subject, body=body, reply_to=_support_email())
        return True
    except Exception as e:
        logger.warning(f"[billing-email] renewal-failed reminder failed: {e}")
        return False
