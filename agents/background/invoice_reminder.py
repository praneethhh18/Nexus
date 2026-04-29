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
import sqlite3
from datetime import date, timedelta

from loguru import logger

from config.settings import DB_PATH
from utils.timez import now_iso, now_utc_naive

# Only re-nag once every N days per invoice
REMINDER_INTERVAL_DAYS = int(os.getenv("INVOICE_REMINDER_INTERVAL_DAYS", "7"))
TAG = "invoice-reminder"


def _already_reminded_recently(business_id: str, invoice_id: str) -> bool:
    from agents.approval_queue import APPROVALS_TABLE
    cutoff = (now_utc_naive() - timedelta(days=REMINDER_INTERVAL_DAYS)).isoformat()
    conn = sqlite3.connect(DB_PATH)
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


def _compose_reminder(invoice: dict, business_name: str) -> dict:
    days_overdue = 0
    due = invoice.get("due_date")
    if due:
        try:
            days_overdue = (date.today() - date.fromisoformat(due)).days
        except Exception as e:
            # Bad date format — fall through to the "a date now past" copy.
            logger.debug(f"[InvoiceReminder] bad due_date {due!r}: {e}")

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
        args = _compose_reminder(inv, business_name)
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
    now = now_iso()
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
            logger.warning(f"[InvoiceReminder] Failed for {r['id']}: {e}")
            results.append({"business_id": r["id"], "error": str(e)})
    return results
