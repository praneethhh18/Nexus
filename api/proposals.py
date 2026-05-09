"""AI Proposal Generator — natural-language brief → structured spec → PDF.

End-to-end:
    1. User says "Generate proposal for Mehta — 5K flyers at Rs 40 each by Diwali"
    2. LLM parses brief → structured proposal_spec (sections, line items, totals)
    3. Optional: auto-merge the recipient's name/title/company from the matched
       CRM contact + business profile for the sender block
    4. ReportLab renders a clean PDF (sender / recipient / scope / line items /
       total / terms / signature block)
    5. PDF saved + returned with a download URL the agent can hand back

Pairs with the existing send_email tool — agent can attach the PDF when
sending the proposal email automatically.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger


# Where generated PDFs land. Lives under data/ so the existing static-files
# mount + cleanup tooling can reach them.
def _proposals_dir() -> Path:
    base = Path(os.getenv("DATA_DIR", "data")) / "proposals"
    base.mkdir(parents=True, exist_ok=True)
    return base


# ── Brief → structured spec via LLM ─────────────────────────────────────────
_SCHEMA_PROMPT = (
    'Reply with ONLY valid JSON in this shape, no markdown / no commentary:\n'
    '{\n'
    '  "title":            "string — short proposal title",\n'
    '  "intro":            "string — 1-2 sentence pitch paragraph",\n'
    '  "scope":            ["string", "string", ...],\n'
    '  "line_items": [\n'
    '    {"description": "string", "qty": number, "unit_price": number, "unit": "string optional"}\n'
    '  ],\n'
    '  "currency":         "string — INR / USD",\n'
    '  "tax_percent":      number,\n'
    '  "terms":            ["string", "string", ...],\n'
    '  "valid_until_days": number,\n'
    '  "delivery_date":    "string — natural date, optional",\n'
    '  "deliverables":     ["string", "string", ...]\n'
    '}\n'
)


def _build_spec(brief: str, *, business_name: str, recipient_name: str) -> Dict[str, Any]:
    """LLM call: natural-language brief → structured spec dict."""
    from config import llm_provider

    system = (
        f"You are a proposal writer for {business_name or 'an Indian SMB'}. "
        f"Convert the user's brief into a clean, professional proposal "
        f"addressed to {recipient_name or 'the client'}. Indian context — "
        f"prefer INR + GST. Keep terms short (3-5 bullets). "
        f"{_SCHEMA_PROMPT}"
    )
    prompt = f"Brief: {brief.strip()}\n\nProposal JSON:"

    try:
        # Drafting is creative — let the router pick cloud if available
        raw = llm_provider.invoke(prompt, system=system, max_tokens=1200,
                                   temperature=0.4, force_cloud=True)
    except Exception as e:
        raise RuntimeError(f"Proposal LLM call failed: {e}")

    # Strip ```json fences if present
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", (raw or "").strip(),
                  flags=re.MULTILINE | re.IGNORECASE)
    try:
        spec = json.loads(raw)
    except json.JSONDecodeError as e:
        logger.warning(f"[proposals] LLM JSON parse failed: {e}; raw start: {raw[:200]!r}")
        raise RuntimeError("LLM didn't return valid JSON — try a clearer brief.")

    # Sanity defaults
    spec.setdefault("title", "Proposal")
    spec.setdefault("intro", "")
    spec.setdefault("scope", [])
    spec.setdefault("line_items", [])
    spec.setdefault("currency", "INR")
    spec.setdefault("tax_percent", 18)  # GST default for India
    spec.setdefault("terms", [
        "50% advance, 50% on delivery",
        "Quote valid for 30 days",
        "GST extra as applicable",
    ])
    spec.setdefault("valid_until_days", 30)
    spec.setdefault("deliverables", [])
    spec.setdefault("delivery_date", "")
    return spec


# ── Spec + business context → PDF ──────────────────────────────────────────
def render_pdf(*, spec: Dict[str, Any], business: Dict[str, Any],
                recipient: Dict[str, Any]) -> bytes:
    """ReportLab renders the proposal. Returns the PDF bytes."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
    )

    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=18 * mm, bottomMargin=18 * mm,
        title=spec.get("title", "Proposal"),
        author=business.get("name", ""),
    )

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"],
                         fontSize=22, leading=26, spaceAfter=4,
                         textColor=colors.HexColor("#0F172A"))
    h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                         fontSize=12, leading=16, spaceAfter=6, spaceBefore=14,
                         textColor=colors.HexColor("#1D4ED8"))
    body = ParagraphStyle("Body", parent=styles["BodyText"],
                           fontSize=10, leading=14, spaceAfter=6,
                           textColor=colors.HexColor("#0F172A"))
    small = ParagraphStyle("Small", parent=body, fontSize=9, leading=12,
                            textColor=colors.HexColor("#475569"))

    story = []

    # ── Header: business name + contact bar
    story.append(Paragraph(business.get("name") or "Your Business", h1))
    bits = [b for b in (business.get("email"), business.get("phone"), business.get("website")) if b]
    if bits:
        story.append(Paragraph(" · ".join(bits), small))
    story.append(Spacer(1, 14))

    # Title block
    story.append(Paragraph(spec.get("title", "Proposal"), h2))
    today = datetime.now().strftime("%d %b %Y")
    valid_until = (datetime.now() + timedelta(days=int(spec.get("valid_until_days", 30)))).strftime("%d %b %Y")
    story.append(Paragraph(f"<b>Date:</b> {today} &nbsp;&nbsp;&nbsp; <b>Valid until:</b> {valid_until}", small))
    story.append(Spacer(1, 8))

    # Recipient
    rec_name = recipient.get("name") or "Client"
    rec_company = recipient.get("company") or ""
    rec_extra = " · ".join([x for x in (recipient.get("email"), recipient.get("phone")) if x])
    story.append(Paragraph(f"<b>To:</b> {rec_name}" + (f" — {rec_company}" if rec_company else ""), body))
    if rec_extra:
        story.append(Paragraph(rec_extra, small))
    story.append(Spacer(1, 12))

    # Intro
    if spec.get("intro"):
        story.append(Paragraph(spec["intro"], body))
        story.append(Spacer(1, 6))

    # Scope
    scope = spec.get("scope") or []
    if scope:
        story.append(Paragraph("Scope of work", h2))
        for item in scope:
            story.append(Paragraph(f"• {item}", body))

    # Line items + totals
    items = spec.get("line_items") or []
    if items:
        story.append(Paragraph("Line items", h2))
        currency = spec.get("currency", "INR")
        symbol = "₹" if currency == "INR" else "$" if currency == "USD" else f"{currency} "
        rows = [["#", "Description", "Qty", "Unit price", "Amount"]]
        subtotal = 0.0
        for i, it in enumerate(items, 1):
            qty = float(it.get("qty") or 1)
            unit = float(it.get("unit_price") or 0)
            amount = qty * unit
            subtotal += amount
            unit_label = it.get("unit", "")
            qty_str = f"{int(qty) if qty.is_integer() else qty}{(' ' + unit_label) if unit_label else ''}"
            rows.append([
                str(i),
                Paragraph(it.get("description", ""), body),
                qty_str,
                f"{symbol}{unit:,.2f}",
                f"{symbol}{amount:,.2f}",
            ])
        tax_pct = float(spec.get("tax_percent") or 0)
        tax_amount = subtotal * tax_pct / 100
        total = subtotal + tax_amount
        rows.append(["", "", "", "Subtotal", f"{symbol}{subtotal:,.2f}"])
        if tax_pct:
            rows.append(["", "", "", f"Tax ({tax_pct:g}%)", f"{symbol}{tax_amount:,.2f}"])
        rows.append(["", "", "", Paragraph("<b>Total</b>", body), Paragraph(f"<b>{symbol}{total:,.2f}</b>", body)])

        col_widths = [10 * mm, 80 * mm, 22 * mm, 28 * mm, 28 * mm]
        tbl = Table(rows, colWidths=col_widths)
        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1D4ED8")),
            ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
            ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",   (0, 0), (-1, -1), 9),
            ("ALIGN",      (2, 1), (-1, -1), "RIGHT"),
            ("VALIGN",     (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("TOPPADDING",    (0, 0), (-1, 0), 6),
            ("LINEBELOW",     (0, 0), (-1, 0), 0.5, colors.HexColor("#0F172A")),
            ("LINEABOVE",     (0, -3), (-1, -3), 0.5, colors.HexColor("#94A3B8")),
            ("LINEABOVE",     (0, -1), (-1, -1), 1.0, colors.HexColor("#0F172A")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -4), [colors.white, colors.HexColor("#F8FAFC")]),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 10))

    # Deliverables
    delivs = spec.get("deliverables") or []
    if delivs:
        story.append(Paragraph("Deliverables", h2))
        for d in delivs:
            story.append(Paragraph(f"• {d}", body))

    # Delivery date
    if spec.get("delivery_date"):
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"<b>Delivery:</b> {spec['delivery_date']}", body))

    # Terms
    terms = spec.get("terms") or []
    if terms:
        story.append(Paragraph("Terms", h2))
        for t in terms:
            story.append(Paragraph(f"• {t}", body))

    # Signature block
    story.append(Spacer(1, 20))
    sig_table = Table([
        ["Accepted by:",                    "For " + (business.get("name") or "us:")],
        ["",                                ""],
        ["_____________________________",  "_____________________________"],
        [Paragraph(rec_name, small),        Paragraph(business.get("name") or "", small)],
    ], colWidths=[85 * mm, 85 * mm])
    sig_table.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 2), (-1, 2), 18),
    ]))
    story.append(sig_table)

    doc.build(story)
    pdf = buf.getvalue()
    buf.close()
    return pdf


# ── Top-level orchestrator ─────────────────────────────────────────────────
def generate_proposal(*, business_id: str, brief: str,
                       contact_id: Optional[str] = None,
                       recipient_overrides: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Brief → spec → PDF. Saves the PDF and returns id, path, and metadata."""
    business = _load_business(business_id)
    recipient = _load_recipient(business_id, contact_id, recipient_overrides)
    spec = _build_spec(
        brief,
        business_name=business.get("name", ""),
        recipient_name=recipient.get("name", ""),
    )
    pdf_bytes = render_pdf(spec=spec, business=business, recipient=recipient)

    pid = f"pr-{uuid.uuid4().hex[:10]}"
    fname = f"{pid}.pdf"
    fpath = _proposals_dir() / fname
    fpath.write_bytes(pdf_bytes)

    return {
        "id":         pid,
        "filename":   fname,
        "path":       str(fpath),
        "size_bytes": len(pdf_bytes),
        "title":      spec.get("title"),
        "spec":       spec,
        "recipient":  recipient,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def _load_business(business_id: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {"name": "", "email": "", "phone": "", "website": ""}
    try:
        from api.businesses import get_business
        b = get_business(business_id) or {}
        out["name"]    = b.get("name", "")
        out["email"]   = b.get("email", "")
        out["phone"]   = b.get("phone", "")
        out["website"] = b.get("website", "")
    except Exception as e:
        logger.debug(f"[proposals] business load fallback: {e}")
    return out


def _load_recipient(business_id: str, contact_id: Optional[str],
                     overrides: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    out = {"name": "", "company": "", "email": "", "phone": ""}
    if contact_id:
        try:
            from api import crm as _crm
            c = _crm.get_contact(business_id, contact_id)
            out["name"]    = " ".join(filter(None, [c.get("first_name"), c.get("last_name")])).strip()
            out["company"] = c.get("company_name", "")
            out["email"]   = c.get("email", "")
            out["phone"]   = c.get("phone", "")
        except Exception as e:
            logger.debug(f"[proposals] contact load fallback for {contact_id}: {e}")
    if overrides:
        for k, v in overrides.items():
            if v:
                out[k] = v
    return out
