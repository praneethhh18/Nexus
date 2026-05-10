"""GST invoice generator for Razorpay-paid subscriptions.

When NexusAgent is GST-registered (BUSINESS_GSTIN env set):
    Issues a proper Tax Invoice with CGST + SGST (intra-state) or IGST
    (inter-state). 18% total split as 9% CGST + 9% SGST or 18% IGST.

When NexusAgent is NOT GST-registered (turnover < ₹20L):
    Issues a "Bill of Supply" — legally distinct, no tax breakdown,
    same metadata. Most Indian SMB customers accept this for accounting.

Inputs:
    payment_id, order_id, plan, amount_inr, customer (name/email/gstin
    optional), date.

Output:
    PDF bytes — caller attaches to the welcome email via Resend.

Why home-grown not a SaaS (Zoho Invoice, etc.)?
    The invoice IS the receipt at this stage. One-off PDF generation is
    cheaper than a SaaS subscription. Move to Zoho when monthly invoice
    volume > 200 OR when you're GST-registered and need automated returns.
"""
from __future__ import annotations

import io
import os
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)


# Visual brand — kept in step with the React frontend.
NEXUS_PURPLE = colors.HexColor("#6366F1")
NEXUS_DARK   = colors.HexColor("#0F172A")
NEXUS_GREY   = colors.HexColor("#64748B")
NEXUS_LIGHT  = colors.HexColor("#F1F5F9")


def _vendor_block() -> dict:
    """Issuer details — read from env so prod and dev don't drift.
    Fall back to sensible defaults if any are missing."""
    return {
        "name":    os.getenv("BUSINESS_LEGAL_NAME", "NexusAgent"),
        "address": os.getenv("BUSINESS_ADDRESS",
                              "3-333 Kalyani House, Tharigudde Bondanthila,\n"
                              "Neermatha, Mangalore — 575029, Karnataka, India"),
        "email":   os.getenv("EMAIL_FROM_ADDRESS_ONLY", "hi@nexusagent.in"),
        "gstin":   (os.getenv("BUSINESS_GSTIN", "") or "").strip(),
        "pan":     (os.getenv("BUSINESS_PAN", "") or "").strip(),
        "state":   os.getenv("BUSINESS_STATE", "Karnataka"),
        "state_code": os.getenv("BUSINESS_STATE_CODE", "29"),  # KA = 29
    }


def _split_tax(amount_inr: float, customer_state_code: str,
               vendor_state_code: str) -> dict:
    """Compute tax breakdown given a total. 18% GST on SaaS as of 2026.
    Same state → CGST 9% + SGST 9%. Different state → IGST 18%."""
    base = amount_inr / 1.18           # backwards-compute pre-tax base
    tax  = amount_inr - base
    if customer_state_code and customer_state_code == vendor_state_code:
        return {
            "type":  "intra-state",
            "base":  round(base, 2),
            "cgst":  round(tax / 2, 2),
            "sgst":  round(tax / 2, 2),
            "igst":  0.0,
            "total": round(amount_inr, 2),
        }
    return {
        "type":  "inter-state",
        "base":  round(base, 2),
        "cgst":  0.0,
        "sgst":  0.0,
        "igst":  round(tax, 2),
        "total": round(amount_inr, 2),
    }


def render_invoice_pdf(
    *,
    payment_id: str,
    order_id: str,
    plan_label: str,
    plan_period: str,
    amount_inr: float,
    customer_name: str,
    customer_email: str,
    customer_gstin: str = "",
    customer_state_code: str = "",
    invoice_date: Optional[datetime] = None,
) -> bytes:
    """Build the PDF in-memory; return its bytes.

    The same generator handles "Tax Invoice" (vendor has GSTIN) and
    "Bill of Supply" (vendor doesn't) — switching the title and tax block
    accordingly. Customer-side GSTIN is optional and printed when given so
    they can claim input-tax credit.
    """
    invoice_date = invoice_date or datetime.now()
    vendor = _vendor_block()
    is_taxed = bool(vendor["gstin"])

    # Document-relative invoice number — date-stamped + payment-id-stamped
    # so it's unique without a sequence table. Format: NX/YYYYMM/<payid suffix>
    invoice_no = f"NX/{invoice_date.strftime('%Y%m')}/{(payment_id or 'X')[-8:].upper()}"

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "InvoiceTitle", parent=styles["Heading1"],
        fontName="Helvetica-Bold", fontSize=18,
        textColor=NEXUS_DARK, alignment=2, spaceAfter=2,  # right-aligned
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        fontName="Helvetica-Bold", fontSize=8.5,
        textColor=NEXUS_GREY, spaceAfter=2,
        leading=10,
    )
    body_style = ParagraphStyle(
        "Body", parent=styles["Normal"],
        fontSize=9.5, textColor=NEXUS_DARK, leading=12,
    )
    story = []

    # ── Header: vendor block (left) + INVOICE title (right) ────────────
    title_text = "TAX INVOICE" if is_taxed else "BILL OF SUPPLY"
    header_table = Table(
        [[
            Paragraph(
                f"<b><font size=13 color='{NEXUS_PURPLE.hexval()}'>NexusAgent</font></b><br/>"
                f"<font size=8 color='{NEXUS_GREY.hexval()}'>"
                f"{vendor['address'].replace(chr(10), '<br/>')}<br/>"
                f"Email: {vendor['email']}<br/>"
                + (f"GSTIN: {vendor['gstin']}<br/>" if vendor['gstin'] else "")
                + (f"PAN: {vendor['pan']}" if vendor['pan'] else "")
                + "</font>",
                body_style,
            ),
            Paragraph(
                f"<b>{title_text}</b><br/>"
                f"<font size=8 color='{NEXUS_GREY.hexval()}'>"
                f"Invoice #: {invoice_no}<br/>"
                f"Date: {invoice_date.strftime('%d %b %Y')}<br/>"
                f"Payment ID: {payment_id}<br/>"
                f"Order ID: {order_id}"
                f"</font>",
                title_style,
            ),
        ]],
        colWidths=[100*mm, 70*mm],
    )
    header_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 6*mm))

    # ── Customer block ────────────────────────────────────────────────
    cust_lines = [f"<b>Bill To</b>", customer_name or "—", customer_email or ""]
    if customer_gstin:
        cust_lines.append(f"GSTIN: {customer_gstin}")
    story.append(Paragraph("<br/>".join(cust_lines), body_style))
    story.append(Spacer(1, 6*mm))

    # ── Line item ─────────────────────────────────────────────────────
    desc = f"NexusAgent — {plan_label} ({plan_period})"
    hsn  = "998313"   # SAC for "Hosting and information technology infrastructure provisioning"
    line_data = [
        ["Description", "HSN/SAC", "Qty", "Rate (₹)", "Amount (₹)"],
        [desc, hsn, "1", f"{amount_inr:,.2f}", f"{amount_inr:,.2f}"],
    ]
    line_table = Table(line_data, colWidths=[80*mm, 20*mm, 14*mm, 28*mm, 28*mm])
    line_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), NEXUS_LIGHT),
        ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",   (0,0), (-1,-1), 9),
        ("TEXTCOLOR",  (0,0), (-1,0), NEXUS_DARK),
        ("BOX",        (0,0), (-1,-1), 0.5, NEXUS_GREY),
        ("INNERGRID",  (0,0), (-1,-1), 0.25, NEXUS_LIGHT),
        ("VALIGN",     (0,0), (-1,-1), "MIDDLE"),
        ("ALIGN",      (1,0), (-1,-1), "RIGHT"),
        ("ALIGN",      (0,0), (0,-1), "LEFT"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 7),
        ("TOPPADDING",    (0,0), (-1,-1), 7),
    ]))
    story.append(line_table)
    story.append(Spacer(1, 4*mm))

    # ── Tax / total block ─────────────────────────────────────────────
    if is_taxed:
        tax = _split_tax(amount_inr, customer_state_code, vendor["state_code"])
        if tax["type"] == "intra-state":
            tax_rows = [
                ["Taxable amount", f"₹ {tax['base']:,.2f}"],
                ["CGST @ 9%",      f"₹ {tax['cgst']:,.2f}"],
                ["SGST @ 9%",      f"₹ {tax['sgst']:,.2f}"],
            ]
        else:
            tax_rows = [
                ["Taxable amount", f"₹ {tax['base']:,.2f}"],
                ["IGST @ 18%",     f"₹ {tax['igst']:,.2f}"],
            ]
        tax_rows.append(["TOTAL",   f"₹ {tax['total']:,.2f}"])
    else:
        # Not GST-registered — just show "Total" (no tax breakdown).
        tax_rows = [["TOTAL", f"₹ {amount_inr:,.2f}"]]

    tax_table = Table(tax_rows, colWidths=[120*mm, 50*mm])
    tax_table.setStyle(TableStyle([
        ("FONTSIZE",     (0,0), (-1,-1), 9.5),
        ("ALIGN",        (-1,0), (-1,-1), "RIGHT"),
        ("ALIGN",        (0,0),  (0,-1),  "RIGHT"),
        ("FONTNAME",     (0,-1), (-1,-1), "Helvetica-Bold"),
        ("BACKGROUND",   (0,-1), (-1,-1), NEXUS_LIGHT),
        ("TEXTCOLOR",    (0,-1), (-1,-1), NEXUS_DARK),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
        ("TOPPADDING",   (0,0), (-1,-1), 5),
        ("LINEABOVE",    (0,-1), (-1,-1), 0.5, NEXUS_GREY),
    ]))
    story.append(tax_table)
    story.append(Spacer(1, 8*mm))

    # ── Footer / notes ────────────────────────────────────────────────
    notes = (
        "<font size=8 color='{grey}'>"
        "Payment received via Razorpay. This is a system-generated document — "
        "no signature required.<br/>"
        "{tax_line}"
        "Questions about this invoice? Reply to this email or write to "
        f"{vendor['email']}."
        "</font>"
    ).format(
        grey=NEXUS_GREY.hexval(),
        tax_line=(
            "Tax amounts shown are inclusive in the total per Section 16 of the "
            "CGST Act, 2017.<br/>" if is_taxed else ""
        ),
    )
    story.append(Paragraph(notes, body_style))

    doc.build(story)
    return buffer.getvalue()
