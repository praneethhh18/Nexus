"""Invoice tools — create, update, render, email."""
from __future__ import annotations

from agents.tool_registry import register_tool
from api import invoices as _inv


def _list_invoices(ctx, args):
    return _inv.list_invoices(
        ctx["business_id"],
        status=args.get("status"),
        search=args.get("search"),
        limit=int(args.get("limit", 50)),
    )


register_tool(
    name="list_invoices",
    description="List invoices for the current business. Filter by status (draft|sent|paid|overdue|cancelled).",
    input_schema={
        "type": "object",
        "properties": {
            "status": {"type": "string"},
            "search": {"type": "string"},
            "limit": {"type": "integer", "default": 50},
        },
    },
    handler=_list_invoices,
)


def _invoice_summary(ctx, args):
    return _inv.invoice_summary(ctx["business_id"])


register_tool(
    name="invoice_summary",
    description="Get invoice totals broken down by status (outstanding, paid, overdue, draft).",
    input_schema={"type": "object", "properties": {}},
    handler=_invoice_summary,
)


def _create_invoice(ctx, args):
    return _inv.create_invoice(ctx["business_id"], ctx["user_id"], args)


register_tool(
    name="create_invoice",
    description=(
        "Create an invoice (in draft status by default). Pass customer_name and "
        "line_items = list of {description, quantity, unit_price}. Optionally link "
        "to a CRM company via customer_company_id or contact via customer_contact_id."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "customer_name": {"type": "string"},
            "customer_email": {"type": "string"},
            "customer_address": {"type": "string"},
            "customer_company_id": {"type": "string"},
            "customer_contact_id": {"type": "string"},
            "currency": {"type": "string", "default": "USD"},
            "issue_date": {"type": "string", "description": "YYYY-MM-DD"},
            "due_date": {"type": "string", "description": "YYYY-MM-DD"},
            "tax_pct": {"type": "number", "default": 0},
            "notes": {"type": "string"},
            "status": {"type": "string", "enum": ["draft", "sent", "paid", "overdue", "cancelled"], "default": "draft"},
            "line_items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "quantity": {"type": "number"},
                        "unit_price": {"type": "number"},
                    },
                    "required": ["description"],
                },
            },
        },
        "required": ["line_items"],
    },
    handler=_create_invoice,
    summary_fn=lambda a: (
        f"Create invoice for {a.get('customer_name', 'customer')} "
        f"({len(a.get('line_items') or [])} line items)"
    ),
)


def _update_invoice(ctx, args):
    iid = args.pop("invoice_id")
    return _inv.update_invoice(ctx["business_id"], iid, args)


register_tool(
    name="update_invoice",
    description="Update an invoice's status, line items, totals, or customer info.",
    input_schema={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string"},
            "status": {"type": "string", "enum": ["draft", "sent", "paid", "overdue", "cancelled"]},
            "customer_name": {"type": "string"},
            "customer_email": {"type": "string"},
            "customer_address": {"type": "string"},
            "due_date": {"type": "string"},
            "issue_date": {"type": "string"},
            "tax_pct": {"type": "number"},
            "notes": {"type": "string"},
            "line_items": {"type": "array"},
        },
        "required": ["invoice_id"],
    },
    handler=_update_invoice,
    summary_fn=lambda a: f"Update invoice {a.get('invoice_id')}",
)


def _mark_paid(ctx, args):
    return _inv.update_invoice(ctx["business_id"], args["invoice_id"], {"status": "paid"})


register_tool(
    name="mark_invoice_paid",
    description="Shortcut: mark an invoice as paid. Stamps paid_at automatically.",
    input_schema={
        "type": "object",
        "properties": {"invoice_id": {"type": "string"}},
        "required": ["invoice_id"],
    },
    handler=_mark_paid,
    summary_fn=lambda a: f"Mark invoice {a.get('invoice_id')} PAID",
)


def _render_invoice(ctx, args):
    from api.businesses import get_business
    biz = get_business(ctx["business_id"])
    path = _inv.render_pdf(ctx["business_id"], args["invoice_id"], business_name=(biz or {}).get("name", ""))
    return {"pdf_path": path}


register_tool(
    name="render_invoice_pdf",
    description="Re-render the PDF for an invoice. Returns the file path.",
    input_schema={
        "type": "object",
        "properties": {"invoice_id": {"type": "string"}},
        "required": ["invoice_id"],
    },
    handler=_render_invoice,
    summary_fn=lambda a: f"Render PDF for invoice {a.get('invoice_id')}",
)


def _send_invoice_email(ctx, args):
    """Send an invoice via email with PDF attached. Always requires approval."""
    invoice_id = args["invoice_id"]
    inv = _inv.get_invoice(ctx["business_id"], invoice_id)
    to = (args.get("to") or inv.get("customer_email") or "").strip()
    if not to:
        raise ValueError("Customer email missing; pass `to` or set it on the invoice first")

    from api.businesses import get_business
    biz = get_business(ctx["business_id"])
    pdf_path = _inv.render_pdf(ctx["business_id"], invoice_id, business_name=(biz or {}).get("name", ""))

    subject = args.get("subject") or f"Invoice {inv['number']} from {(biz or {}).get('name', 'NexusAgent')}"
    body = args.get("body") or (
        f"Hello {inv.get('customer_name', '')},\n\n"
        f"Please find attached invoice {inv['number']} "
        f"for {inv['total']:,.2f} {inv['currency']}, due {inv.get('due_date') or 'upon receipt'}.\n\n"
        f"Thank you,\n{(biz or {}).get('name', 'NexusAgent')}"
    )

    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    if not EMAIL_ENABLED:
        raise ValueError("Email not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD.")

    import smtplib
    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.mime.base import MIMEBase
    from email import encoders
    from pathlib import Path

    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    p = Path(pdf_path)
    if p.exists():
        with open(p, "rb") as fh:
            part = MIMEBase("application", "pdf")
            part.set_payload(fh.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{p.name}"')
        msg.attach(part)

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
        server.send_message(msg)

    # Auto-advance status if it was draft
    if inv["status"] == "draft":
        _inv.update_invoice(ctx["business_id"], invoice_id, {"status": "sent"})
    return {"sent": True, "to": to, "subject": subject}


register_tool(
    name="send_invoice_email",
    description=(
        "Email an invoice to the customer with the PDF attached. Always requires "
        "approval. If `to` is not provided, uses the invoice's customer_email. "
        "Auto-advances status from draft to sent."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "invoice_id": {"type": "string"},
            "to": {"type": "string", "description": "Override recipient email"},
            "subject": {"type": "string"},
            "body": {"type": "string"},
        },
        "required": ["invoice_id"],
    },
    handler=_send_invoice_email,
    summary_fn=lambda a: f"EMAIL invoice {a.get('invoice_id')} to {a.get('to') or 'customer on file'}",
)


def _delete_invoice(ctx, args):
    _inv.delete_invoice(ctx["business_id"], args["invoice_id"])
    return {"ok": True}


register_tool(
    name="delete_invoice",
    description="Delete an invoice. Requires approval.",
    input_schema={
        "type": "object",
        "properties": {"invoice_id": {"type": "string"}},
        "required": ["invoice_id"],
    },
    handler=_delete_invoice,
    summary_fn=lambda a: f"DELETE invoice {a.get('invoice_id')}",
)
