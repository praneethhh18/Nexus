"""
Invoices module — per-business invoice numbering, line items, and PDF generation.

Schema: one row per invoice header, line items stored as JSON inside the invoice
row (keeps it simple and avoids N+1 queries). Totals are computed on write and
recomputed on every update.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from loguru import logger

from config.settings import DB_PATH, OUTPUTS_DIR

INVOICES_TABLE = "nexus_invoices"
COUNTER_TABLE = "nexus_invoice_counters"

STATUSES = ("draft", "sent", "paid", "overdue", "cancelled")

INVOICE_DIR = Path(OUTPUTS_DIR) / "invoices"


def _get_conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {INVOICES_TABLE} (
        id TEXT PRIMARY KEY,
        business_id TEXT NOT NULL,
        number TEXT NOT NULL,
        status TEXT DEFAULT 'draft',
        customer_company_id TEXT,
        customer_contact_id TEXT,
        customer_name TEXT,
        customer_email TEXT,
        customer_address TEXT DEFAULT '',
        currency TEXT DEFAULT 'USD',
        issue_date TEXT,
        due_date TEXT,
        notes TEXT DEFAULT '',
        line_items TEXT DEFAULT '[]',
        subtotal REAL DEFAULT 0,
        tax_pct REAL DEFAULT 0,
        tax_amount REAL DEFAULT 0,
        total REAL DEFAULT 0,
        pdf_path TEXT,
        paid_at TEXT,
        created_at TEXT,
        updated_at TEXT,
        created_by TEXT
    )""")
    conn.execute(f"CREATE UNIQUE INDEX IF NOT EXISTS idx_invoice_biz_number ON {INVOICES_TABLE}(business_id, number)")
    conn.execute(f"CREATE INDEX IF NOT EXISTS idx_invoice_status ON {INVOICES_TABLE}(business_id, status)")

    # Additive migration for recurring invoices — safe to re-run.
    for col, decl in [
        ("recurrence", "TEXT DEFAULT 'none'"),
        ("recurrence_parent_id", "TEXT"),
    ]:
        existing = [r[1] for r in conn.execute(f"PRAGMA table_info({INVOICES_TABLE})").fetchall()]
        if col not in existing:
            conn.execute(f"ALTER TABLE {INVOICES_TABLE} ADD COLUMN {col} {decl}")

    conn.execute(f"""
    CREATE TABLE IF NOT EXISTS {COUNTER_TABLE} (
        business_id TEXT PRIMARY KEY,
        last_number INTEGER DEFAULT 0
    )""")

    conn.commit()
    return conn


INVOICE_RECURRENCES = ("none", "weekly", "monthly")


def _next_number(business_id: str) -> str:
    """Generate the next invoice number for a business (format: INV-YYYY-0001)."""
    conn = _get_conn()
    try:
        row = conn.execute(
            f"SELECT last_number FROM {COUNTER_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchone()
        current = row[0] if row else 0
        next_num = current + 1
        if row:
            conn.execute(
                f"UPDATE {COUNTER_TABLE} SET last_number = ? WHERE business_id = ?",
                (next_num, business_id),
            )
        else:
            conn.execute(
                f"INSERT INTO {COUNTER_TABLE} (business_id, last_number) VALUES (?, ?)",
                (business_id, next_num),
            )
        conn.commit()
    finally:
        conn.close()
    year = datetime.now().year
    return f"INV-{year}-{next_num:04d}"


def _validate_text(val: str, field: str, max_len: int = 400) -> str:
    val = (val or "").strip()
    if len(val) > max_len:
        raise HTTPException(400, f"{field} too long (max {max_len} chars)")
    return val


def _validate_date(s: Optional[str], field: str) -> Optional[str]:
    if not s:
        return None
    s = s.strip()
    try:
        if len(s) == 10:
            datetime.strptime(s, "%Y-%m-%d")
            return s
        return datetime.fromisoformat(s.replace("Z", "+00:00")).date().isoformat()
    except Exception:
        raise HTTPException(400, f"Invalid {field} format: {s} (use YYYY-MM-DD)")


def _validate_line_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize line items: {description, quantity, unit_price, amount}."""
    if not isinstance(items, list):
        raise HTTPException(400, "line_items must be a list")
    if len(items) > 200:
        raise HTTPException(400, "Too many line items (max 200)")
    normalized = []
    for idx, it in enumerate(items):
        if not isinstance(it, dict):
            raise HTTPException(400, f"Line item {idx} must be an object")
        desc = (it.get("description") or "").strip()
        if not desc:
            raise HTTPException(400, f"Line item {idx} is missing description")
        if len(desc) > 400:
            raise HTTPException(400, f"Line item {idx} description too long")
        try:
            qty = float(it.get("quantity", 1) or 0)
            price = float(it.get("unit_price", 0) or 0)
        except (TypeError, ValueError):
            raise HTTPException(400, f"Line item {idx} has invalid number")
        if qty < 0 or price < 0 or qty > 1e9 or price > 1e9:
            raise HTTPException(400, f"Line item {idx} quantity/price out of range")
        amount = round(qty * price, 2)
        normalized.append({
            "description": desc,
            "quantity": qty,
            "unit_price": price,
            "amount": amount,
        })
    return normalized


def _compute_totals(line_items: List[Dict], tax_pct: float) -> Dict[str, float]:
    subtotal = round(sum(it["amount"] for it in line_items), 2)
    tax_amount = round(subtotal * (tax_pct / 100.0), 2)
    total = round(subtotal + tax_amount, 2)
    return {"subtotal": subtotal, "tax_amount": tax_amount, "total": total}


def _now() -> str:
    return datetime.now().isoformat()


# ═══════════════════════════════════════════════════════════════════════════════
#  CRUD
# ═══════════════════════════════════════════════════════════════════════════════
def create_invoice(business_id: str, user_id: str, data: Dict[str, Any]) -> Dict:
    from api import crm as _crm

    customer_company_id = data.get("customer_company_id") or None
    customer_contact_id = data.get("customer_contact_id") or None

    customer_name = _validate_text(data.get("customer_name", ""), "Customer name", 200)
    customer_email = _validate_text(data.get("customer_email", ""), "Customer email", 200)

    # If linked to a CRM company, pull name as fallback
    if customer_company_id:
        co = _crm.get_company(business_id, customer_company_id)
        if not customer_name:
            customer_name = co["name"]
    if customer_contact_id:
        ct = _crm.get_contact(business_id, customer_contact_id)
        if not customer_email:
            customer_email = ct.get("email") or ""
        if not customer_name:
            customer_name = (ct["first_name"] + " " + ct["last_name"]).strip()

    if not customer_name:
        raise HTTPException(400, "Either customer_name, customer_company_id, or customer_contact_id is required")

    line_items = _validate_line_items(data.get("line_items", []))
    try:
        tax_pct = float(data.get("tax_pct", 0) or 0)
    except (TypeError, ValueError):
        tax_pct = 0
    if tax_pct < 0 or tax_pct > 100:
        raise HTTPException(400, "tax_pct must be between 0 and 100")

    totals = _compute_totals(line_items, tax_pct)

    status = data.get("status", "draft")
    if status not in STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(STATUSES)}")

    issue = _validate_date(data.get("issue_date"), "issue_date") or date.today().isoformat()
    due = _validate_date(data.get("due_date"), "due_date")

    currency = _validate_text(data.get("currency", "USD"), "Currency", 8) or "USD"

    recurrence = (data.get("recurrence") or "none").strip().lower()
    if recurrence not in INVOICE_RECURRENCES:
        raise HTTPException(400, f"Invalid recurrence. Must be one of: {', '.join(INVOICE_RECURRENCES)}")
    recurrence_parent_id = data.get("recurrence_parent_id") or None

    iid = f"inv-{uuid.uuid4().hex[:10]}"
    number = _next_number(business_id)

    row = (
        iid, business_id, number, status,
        customer_company_id, customer_contact_id,
        customer_name, customer_email,
        _validate_text(data.get("customer_address", ""), "Customer address", 500),
        currency,
        issue, due,
        _validate_text(data.get("notes", ""), "Notes", 2000),
        json.dumps(line_items),
        totals["subtotal"], tax_pct, totals["tax_amount"], totals["total"],
        None, None, _now(), _now(), user_id,
        recurrence, recurrence_parent_id,
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {INVOICES_TABLE} "
            f"(id, business_id, number, status, customer_company_id, customer_contact_id, "
            f"customer_name, customer_email, customer_address, currency, issue_date, due_date, "
            f"notes, line_items, subtotal, tax_pct, tax_amount, total, pdf_path, paid_at, "
            f"created_at, updated_at, created_by, recurrence, recurrence_parent_id) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row,
        )
        conn.commit()
    finally:
        conn.close()
    return get_invoice(business_id, iid)


def get_invoice(business_id: str, invoice_id: str) -> Dict:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(
            f"SELECT * FROM {INVOICES_TABLE} WHERE id = ? AND business_id = ?",
            (invoice_id, business_id),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(404, "Invoice not found")
    d = dict(row)
    d["line_items"] = json.loads(d["line_items"] or "[]")
    return d


def list_invoices(
    business_id: str,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
) -> List[Dict]:
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        sql = f"SELECT * FROM {INVOICES_TABLE} WHERE business_id = ?"
        params: list = [business_id]
        if status:
            if status not in STATUSES:
                raise HTTPException(400, f"Invalid status: {status}")
            sql += " AND status = ?"
            params.append(status)
        if search:
            sql += " AND (number LIKE ? OR customer_name LIKE ? OR customer_email LIKE ?)"
            s = f"%{search}%"
            params.extend([s, s, s])
        sql += " ORDER BY issue_date DESC, created_at DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    finally:
        conn.close()
    result = []
    for r in rows:
        d = dict(r)
        d["line_items"] = json.loads(d["line_items"] or "[]")
        result.append(d)
    return result


def update_invoice(business_id: str, invoice_id: str, updates: Dict[str, Any]) -> Dict:
    current = get_invoice(business_id, invoice_id)
    allowed = {"customer_name", "customer_email", "customer_address",
               "currency", "issue_date", "due_date", "notes",
               "line_items", "tax_pct", "status", "recurrence"}
    fields = {k: v for k, v in updates.items() if k in allowed}
    if not fields:
        raise HTTPException(400, "No editable fields provided")

    if "status" in fields and fields["status"] not in STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(STATUSES)}")
    if "recurrence" in fields:
        fields["recurrence"] = (fields["recurrence"] or "none").strip().lower()
        if fields["recurrence"] not in INVOICE_RECURRENCES:
            raise HTTPException(400, f"Invalid recurrence. Must be one of: {', '.join(INVOICE_RECURRENCES)}")
    if "issue_date" in fields:
        fields["issue_date"] = _validate_date(fields["issue_date"], "issue_date")
    if "due_date" in fields:
        fields["due_date"] = _validate_date(fields["due_date"], "due_date")
    if "customer_name" in fields:
        fields["customer_name"] = _validate_text(fields["customer_name"], "Customer name", 200)
    if "customer_email" in fields:
        fields["customer_email"] = _validate_text(fields["customer_email"], "Customer email", 200)
    if "customer_address" in fields:
        fields["customer_address"] = _validate_text(fields["customer_address"], "Customer address", 500)
    if "notes" in fields:
        fields["notes"] = _validate_text(fields["notes"], "Notes", 2000)
    if "currency" in fields:
        fields["currency"] = _validate_text(fields["currency"], "Currency", 8)

    # Recompute totals whenever line_items or tax_pct changes
    recompute = "line_items" in fields or "tax_pct" in fields
    if "line_items" in fields:
        fields["line_items"] = _validate_line_items(fields["line_items"])
    if "tax_pct" in fields:
        try:
            fields["tax_pct"] = float(fields["tax_pct"])
        except (TypeError, ValueError):
            raise HTTPException(400, "tax_pct must be a number")
        if fields["tax_pct"] < 0 or fields["tax_pct"] > 100:
            raise HTTPException(400, "tax_pct must be between 0 and 100")

    if recompute:
        items = fields.get("line_items", current["line_items"])
        tax = fields.get("tax_pct", current["tax_pct"])
        totals = _compute_totals(items, tax)
        fields["subtotal"] = totals["subtotal"]
        fields["tax_amount"] = totals["tax_amount"]
        fields["total"] = totals["total"]

    # Status transitions
    extra_sets = []
    extra_params: list = []
    if fields.get("status") == "paid":
        extra_sets.append("paid_at = ?")
        extra_params.append(_now())
    elif "status" in fields and fields["status"] != "paid":
        extra_sets.append("paid_at = NULL")

    # Serialize line_items if present
    fields_for_sql = {}
    for k, v in fields.items():
        fields_for_sql[k] = json.dumps(v) if k == "line_items" else v

    sets = ", ".join(f"{k} = ?" for k in fields_for_sql)
    if extra_sets:
        sets += ", " + ", ".join(extra_sets)
    params = list(fields_for_sql.values()) + extra_params + [_now(), invoice_id, business_id]
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {INVOICES_TABLE} SET {sets}, updated_at = ? WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()

    # When a recurring invoice is marked paid, spawn the next occurrence as a
    # draft so the user doesn't have to recreate the monthly invoice manually.
    if fields.get("status") == "paid":
        try:
            spawn_next_if_recurring(business_id, invoice_id)
        except Exception as e:
            logger.warning(f"[invoices] spawn_next_if_recurring failed for {invoice_id}: {e}")

    return get_invoice(business_id, invoice_id)


def _next_invoice_dates(current_issue: Optional[str], current_due: Optional[str],
                        recurrence: str):
    """Compute (issue_date, due_date) for the next occurrence."""
    from datetime import date as _date, timedelta as _td
    step = {"weekly": 7, "monthly": 30}.get(recurrence)
    if not step:
        return None, None
    try:
        issue = (_date.fromisoformat(current_issue) + _td(days=step)).isoformat() \
            if current_issue else _date.today().isoformat()
    except Exception:
        issue = _date.today().isoformat()
    try:
        due = (_date.fromisoformat(current_due) + _td(days=step)).isoformat() \
            if current_due else None
    except Exception:
        due = None
    return issue, due


def spawn_next_if_recurring(business_id: str, paid_invoice_id: str) -> Optional[Dict]:
    """If the invoice is part of a recurring series and just got paid,
    create the next draft. Idempotent — no duplicates."""
    src = get_invoice(business_id, paid_invoice_id)
    recurrence = (src.get("recurrence") or "none").lower()
    if recurrence == "none":
        return None
    if src.get("status") != "paid":
        return None
    parent_id = src.get("recurrence_parent_id") or src["id"]
    conn = _get_conn()
    conn.row_factory = sqlite3.Row
    try:
        existing = conn.execute(
            f"SELECT id FROM {INVOICES_TABLE} "
            f"WHERE business_id = ? AND recurrence_parent_id = ? AND status IN ('draft','sent')",
            (business_id, parent_id),
        ).fetchone()
    finally:
        conn.close()
    if existing:
        return None
    new_issue, new_due = _next_invoice_dates(src.get("issue_date"), src.get("due_date"), recurrence)
    spawn_data = {
        "customer_company_id": src.get("customer_company_id"),
        "customer_contact_id": src.get("customer_contact_id"),
        "customer_name": src.get("customer_name", ""),
        "customer_email": src.get("customer_email", ""),
        "customer_address": src.get("customer_address", ""),
        "currency": src.get("currency", "USD"),
        "issue_date": new_issue,
        "due_date": new_due,
        "notes": src.get("notes", ""),
        "line_items": src.get("line_items", []),
        "tax_pct": src.get("tax_pct", 0),
        "status": "draft",
        "recurrence": recurrence,
        "recurrence_parent_id": parent_id,
    }
    return create_invoice(business_id, src.get("created_by") or "system", spawn_data)


def delete_invoice(business_id: str, invoice_id: str) -> None:
    inv = get_invoice(business_id, invoice_id)
    # Remove PDF file if present (but only if under our invoice dir)
    pdf = inv.get("pdf_path")
    if pdf:
        try:
            p = Path(pdf)
            if p.is_file() and INVOICE_DIR in p.parents:
                p.unlink(missing_ok=True)
        except Exception:
            pass
    conn = _get_conn()
    try:
        conn.execute(f"DELETE FROM {INVOICES_TABLE} WHERE id = ? AND business_id = ?", (invoice_id, business_id))
        conn.commit()
    finally:
        conn.close()


# ═══════════════════════════════════════════════════════════════════════════════
#  PDF RENDERING
# ═══════════════════════════════════════════════════════════════════════════════
def render_pdf(business_id: str, invoice_id: str, business_name: str = "") -> str:
    """Render the invoice to PDF and return the file path."""
    inv = get_invoice(business_id, invoice_id)
    INVOICE_DIR.mkdir(parents=True, exist_ok=True)

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable,
    )

    ACCENT = colors.HexColor("#1e3a5f")
    LIGHT = colors.HexColor("#f1f5f9")

    filename = f"{inv['number']}.pdf"
    out_path = INVOICE_DIR / filename

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("title", parent=styles["Title"], textColor=ACCENT, fontSize=28, alignment=0)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], textColor=ACCENT, fontSize=11)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, textColor=colors.HexColor("#0f172a"))
    small = ParagraphStyle("small", parent=styles["BodyText"], fontSize=8, textColor=colors.grey)

    doc = SimpleDocTemplate(
        str(out_path), pagesize=A4,
        topMargin=2 * cm, bottomMargin=2 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
    )

    story = []

    # Header: INVOICE title + number
    header_table = Table([
        [Paragraph("<b>INVOICE</b>", title_style),
         Paragraph(f"<b>#{inv['number']}</b><br/><font size=9 color='#64748b'>"
                   f"Issued: {inv['issue_date'] or ''}<br/>Due: {inv['due_date'] or '—'}</font>", body)],
    ], colWidths=[10 * cm, 7 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "RIGHT"),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.4 * cm))
    story.append(HRFlowable(color=ACCENT, thickness=1.5))
    story.append(Spacer(1, 0.6 * cm))

    # From / Bill to
    from_block = f"<b>{business_name or 'NexusAgent Business'}</b>"
    to_block = f"<b>Bill to</b><br/>{inv['customer_name']}"
    if inv.get("customer_email"):
        to_block += f"<br/>{inv['customer_email']}"
    if inv.get("customer_address"):
        to_block += f"<br/>{inv['customer_address'].replace(chr(10), '<br/>')}"

    addr = Table([[Paragraph(from_block, body), Paragraph(to_block, body)]],
                 colWidths=[8.5 * cm, 8.5 * cm])
    addr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(addr)
    story.append(Spacer(1, 0.6 * cm))

    # Line items table
    currency = inv.get("currency", "USD")
    header = ["Description", "Qty", f"Unit ({currency})", f"Amount ({currency})"]
    rows = [header]
    for it in inv["line_items"]:
        rows.append([
            Paragraph(it["description"], body),
            f"{it['quantity']:g}",
            f"{it['unit_price']:,.2f}",
            f"{it['amount']:,.2f}",
        ])
    items_table = Table(rows, colWidths=[9.5 * cm, 1.8 * cm, 3 * cm, 3 * cm])
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 10),
        ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
        ("LINEBELOW", (0, 0), (-1, -1), 0.25, colors.HexColor("#cbd5e1")),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 0.4 * cm))

    # Totals block
    totals_rows = [
        ["Subtotal", f"{inv['subtotal']:,.2f} {currency}"],
        [f"Tax ({inv['tax_pct']:g}%)", f"{inv['tax_amount']:,.2f} {currency}"],
        ["Total", f"{inv['total']:,.2f} {currency}"],
    ]
    totals_table = Table(totals_rows, colWidths=[3 * cm, 3 * cm], hAlign="RIGHT")
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, 1), 9),
        ("FONTSIZE", (0, 2), (-1, 2), 11),
        ("FONTNAME", (0, 2), (-1, 2), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 2), (-1, 2), ACCENT),
        ("LINEABOVE", (0, 2), (-1, 2), 1, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.6 * cm))

    # Notes
    if inv.get("notes"):
        story.append(Paragraph("<b>Notes</b>", h2))
        story.append(Paragraph(inv["notes"].replace("\n", "<br/>"), body))
        story.append(Spacer(1, 0.4 * cm))

    # Footer
    story.append(HRFlowable(color=colors.HexColor("#cbd5e1"), thickness=0.5))
    story.append(Spacer(1, 0.2 * cm))
    story.append(Paragraph(
        f"Generated by NexusAgent · {datetime.now().strftime('%Y-%m-%d %H:%M')}", small,
    ))

    doc.build(story)

    # Save path to DB
    conn = _get_conn()
    try:
        conn.execute(
            f"UPDATE {INVOICES_TABLE} SET pdf_path = ?, updated_at = ? WHERE id = ? AND business_id = ?",
            (str(out_path), _now(), invoice_id, business_id),
        )
        conn.commit()
    finally:
        conn.close()

    logger.info(f"[Invoice] Rendered {inv['number']} → {out_path}")
    return str(out_path)


# ═══════════════════════════════════════════════════════════════════════════════
#  SUMMARY
# ═══════════════════════════════════════════════════════════════════════════════
def invoice_summary(business_id: str) -> Dict[str, Any]:
    conn = _get_conn()
    try:
        def _sum_by(status_tuple):
            placeholders = ",".join("?" for _ in status_tuple)
            row = conn.execute(
                f"SELECT COUNT(*), COALESCE(SUM(total), 0) FROM {INVOICES_TABLE} "
                f"WHERE business_id = ? AND status IN ({placeholders})",
                (business_id,) + status_tuple,
            ).fetchone()
            return {"count": row[0], "total": float(row[1] or 0)}

        outstanding = _sum_by(("sent", "overdue"))
        paid = _sum_by(("paid",))
        draft = _sum_by(("draft",))

        # Overdue: status='sent' but due_date < today
        today = date.today().isoformat()
        overdue_row = conn.execute(
            f"SELECT COUNT(*), COALESCE(SUM(total), 0) FROM {INVOICES_TABLE} "
            f"WHERE business_id = ? AND status = 'sent' AND due_date IS NOT NULL AND due_date < ?",
            (business_id, today),
        ).fetchone()
    finally:
        conn.close()
    return {
        "outstanding": outstanding,
        "paid": paid,
        "draft": draft,
        "overdue": {"count": overdue_row[0], "total": float(overdue_row[1] or 0)},
    }


# ═══════════════════════════════════════════════════════════════════════════════
#  Bulk helpers
# ═══════════════════════════════════════════════════════════════════════════════
def bulk_delete_invoices(business_id: str, ids: List[str]) -> int:
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    conn = _get_conn()
    try:
        cur = conn.execute(
            f"DELETE FROM {INVOICES_TABLE} "
            f"WHERE business_id = ? AND id IN ({placeholders})",
            [business_id, *ids],
        )
        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()


def bulk_update_invoice_status(business_id: str, ids: List[str], status: str) -> int:
    """Mark many invoices with a new status (draft / sent / paid / void)."""
    valid = ("draft", "sent", "paid", "void")
    if status not in valid:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(valid)}")
    if not ids:
        return 0
    placeholders = ",".join("?" for _ in ids)
    conn = _get_conn()
    try:
        cur = conn.execute(
            f"UPDATE {INVOICES_TABLE} SET status = ?, updated_at = ? "
            f"WHERE business_id = ? AND id IN ({placeholders})",
            [status, _now(), business_id, *ids],
        )
        conn.commit()
        return cur.rowcount or 0
    finally:
        conn.close()
