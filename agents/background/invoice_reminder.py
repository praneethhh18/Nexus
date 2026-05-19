"""
Invoice reminder agent — every morning, find invoices that are overdue
and queue a polite reminder email for the owner to approve.

Safe by design:
- Never sends email directly; always via the approval queue.
- One reminder per invoice per X days (configurable), avoiding nag spam.
- Skips invoices without a customer email.
"""
from __future__ import annotations

import os
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import date, timedelta

from loguru import logger

from config.db import get_conn
from utils.timez import now_utc_naive

# Only re-nag once every N days per invoice
REMINDER_INTERVAL_DAYS = int(os.getenv("INVOICE_REMINDER_INTERVAL_DAYS", "7"))
TAG = "invoice-reminder"


def _already_reminded_recently(business_id: str, invoice_id: str) -> bool:
    from agents.approval_queue import APPROVALS_TABLE
    cutoff = (now_utc_naive() - timedelta(days=REMINDER_INTERVAL_DAYS)).isoformat()
    conn = get_conn()
    try:
        row = conn.execute(
            f"SELECT 1 FROM {APPROVALS_TABLE} "
            f"WHERE business_id = ? AND tool_name = 'send_invoice_email' "
            f"AND args_json LIKE ? AND created_at > ? LIMIT 1",
            (business_id, f'%"invoice_id": "{invoice_id}"%', cutoff),
        ).fetchone()
    finally:
        conn.close()
    return bool(row)


# Keywords (case-insensitive) that identify a workspace's "payment reminder"
# email template. The matcher prefers more-specific terms first so a template
# called "Payment reminder" wins over one called just "Reminder".
_PAYMENT_TEMPLATE_KEYWORDS = (
    "payment reminder", "payment / fee reminder", "pending bill",
    "fee reminder", "fee installment", "outstanding payment",
    "overdue payment", "milestone payment", "payment follow-up",
    "payment", "reminder",
)


def _find_payment_template(business_id: str) -> dict | None:
    """Pick the best-matching email template from the workspace's library
    for an invoice-reminder context. We prefer a template named with
    'payment' / 'fee' / 'reminder' so industry-authentic copy is reused
    (Finance shop has 'Payment / fee reminder', Manufacturing has
    'Payment follow-up', Healthcare has 'Pending bill reminder', etc.).
    Returns None if nothing matches — caller falls back to the generic
    composed copy below."""
    try:
        from api import email_templates as _tpl
        templates = _tpl.list_templates(business_id) or []
    except Exception as e:
        logger.debug(f"[InvoiceReminder] template lookup failed: {e}")
        return None
    if not templates:
        return None
    # Lower-case template names once; scan most-specific keyword first.
    indexed = [(t, (t.get("name") or "").lower()) for t in templates]
    for kw in _PAYMENT_TEMPLATE_KEYWORDS:
        for t, nm in indexed:
            if kw in nm:
                return t
    return None


def _fill_template(tpl_body: str, ctx: dict) -> str:
    """Substitute {{var}} tokens from `ctx` into the template body. Tokens
    not in `ctx` are left as-is so the reviewer can fill them or strip them
    before approving the action. Avoids importing a templating engine for
    this single use site."""
    import re as _re
    def _sub(m):
        key = m.group(1).strip()
        return str(ctx.get(key, m.group(0)))
    return _re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", _sub, tpl_body or "")


def _compose_reminder(invoice: dict, business_name: str, *, business_id: str | None = None) -> dict:
    days_overdue = 0
    due = invoice.get("due_date")
    if due:
        try:
            days_overdue = (date.today() - date.fromisoformat(due)).days
        except Exception as e:
            # Bad date format — fall through to the "a date now past" copy.
            logger.debug(f"[InvoiceReminder] bad due_date {due!r}: {e}")

    # ── Prefer the workspace's industry-tuned template if one exists ──
    # The template will have been seeded during onboarding (industry_setup
    # creates "Payment reminder" / "Pending bill reminder" / "Outstanding
    # payment" depending on industry). Falls back to inline copy below
    # so workspaces without templates (or where the matcher missed) still
    # get a reminder.
    if business_id:
        tpl = _find_payment_template(business_id)
        if tpl:
            ctx = {
                # generic CRM fields the template might reference
                "first_name":      (invoice.get("customer_name") or "there").split()[0],
                "last_name":       (invoice.get("customer_name") or "").split()[-1] if invoice.get("customer_name") else "",
                "salutation":      "Mr/Ms",
                "customer_name":   invoice.get("customer_name") or "there",
                "business_name":   business_name,
                "sender_name":     business_name,
                "invoice_number":  invoice["number"],
                "amount":          f"{invoice['total']:,.2f}",
                "due_date":        invoice.get("due_date") or "the original due date",
                "days_overdue":    str(days_overdue),
                # industry-specific tokens — left as-is if the template uses
                # them and the workspace hasn't filled them in
                "upi_id":          "your registered UPI",
                "bank_details":    "the bank details on the invoice",
            }
            subject_filled = _fill_template(tpl.get("subject") or "", ctx) \
                or f"Reminder — invoice {invoice['number']}"
            body_filled = _fill_template(tpl.get("body") or "", ctx)
            return {
                "invoice_id": invoice["id"],
                "to":         invoice.get("customer_email", ""),
                "subject":    subject_filled,
                "body":       body_filled,
                "_template":  tpl.get("name") or "",
            }

    # Generic fallback — kept verbatim from the pre-template behaviour so
    # workspaces without industry-tuned templates still get a reminder.
    subject = f"Friendly reminder — invoice {invoice['number']} is past due"
    body = (
        f"Hi {invoice.get('customer_name', 'there')},\n\n"
        f"I hope you're well. This is a gentle reminder that invoice "
        f"{invoice['number']} for {invoice['total']:,.2f} {invoice['currency']} "
        f"was due on {invoice.get('due_date') or 'a date now past'}"
        + (f" ({days_overdue} days ago)" if days_overdue > 0 else "")
        + ".\n\n"
        f"The invoice is attached to this email. If you've already paid, "
        f"please disregard — and thank you!\n\n"
        f"Best regards,\n{business_name}"
    )
    return {"invoice_id": invoice["id"], "to": invoice.get("customer_email", ""), "subject": subject, "body": body}


def run_for_business(business_id: str) -> dict:
    """Find overdue invoices and queue reminder emails."""
    from api import invoices as _inv
    from api.businesses import get_business
    from agents import approval_queue

    biz = get_business(business_id) or {}
    business_name = biz.get("name", "NexusAgent")

    # Find open invoices with a due_date in the past
    today = date.today().isoformat()
    candidates = []
    for inv in _inv.list_invoices(business_id, limit=500):
        if inv.get("status") != "sent":
            continue
        due = inv.get("due_date")
        if not due or due >= today:
            continue
        if not (inv.get("customer_email") or "").strip():
            continue
        if _already_reminded_recently(business_id, inv["id"]):
            continue
        candidates.append(inv)

    queued = 0
    for inv in candidates:
        # Pass business_id so the composer can pick the workspace's
        # industry-tuned payment template if one exists.
        args = _compose_reminder(inv, business_name, business_id=business_id)
        summary = f"Reminder email for invoice {inv['number']} to {args['to']} ({inv['total']:,.2f} {inv['currency']})"
        try:
            approval_queue.queue_action(
                business_id=business_id,
                user_id=inv.get("created_by") or "system",
                tool_name="send_invoice_email",
                summary=summary,
                args=args,
                ttl_hours=72,
            )
            queued += 1
        except Exception as e:
            logger.warning(f"[InvoiceReminder] queue failed for {inv['id']}: {e}")

    # Also mark invoices that are past due but still 'sent' as 'overdue' for UI clarity
    for inv in candidates:
        try:
            _inv.update_invoice(business_id, inv["id"], {"status": "overdue"})
        except Exception as e:
            logger.warning(f"[InvoiceReminder] mark-overdue failed for invoice {inv['id']}: {e}")

    if queued:
        try:
            from api import notifications as _notifs
            _notifs.push(
                title="Invoice reminders ready",
                message=f"{queued} overdue invoice{'s' if queued != 1 else ''} drafted and waiting for your approval.",
                severity="warning",
                type="agent",
                business_id=business_id,
            )
        except Exception as e:
            logger.warning(f"[InvoiceReminder] notification push failed: {e}")

    logger.info(f"[InvoiceReminder] biz={business_id} candidates={len(candidates)} queued={queued}")
    return {"business_id": business_id, "candidates": len(candidates), "queued": queued}


def run_for_all_businesses() -> list:
    from api.businesses import BUSINESSES_TABLE
    results = []
    conn = get_conn()
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
            logger.warning(f"[InvoiceReminder] Failed for {r['id']}: {e}")
            results.append({"business_id": r["id"], "error": str(e)})
    return results
