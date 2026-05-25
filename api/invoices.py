"""
Invoices module — per-business invoice numbering, line items, and PDF generation.

Schema: one row per invoice header, line items stored as JSON inside the invoice
row (keeps it simple and avoids N+1 queries). Totals are computed on write and
recomputed on every update.
"""
from __future__ import annotations

import json
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Optional, List, Dict, Any

from fastapi import HTTPException
from loguru import logger

from config.settings import OUTPUTS_DIR
from config.db import get_conn, list_columns

INVOICES_TABLE = "nexus_invoices"
COUNTER_TABLE = "nexus_invoice_counters"

STATUSES = ("draft", "sent", "paid", "overdue", "cancelled")

INVOICE_DIR = Path(OUTPUTS_DIR) / "invoices"


def _get_conn():
    conn = get_conn()
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
        currency TEXT DEFAULT 'INR',
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
        existing = list_columns(conn, INVOICES_TABLE)
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


def _validate_line_items(items: List[Dict[str, Any]],
                         default_gst_rate: float = 0.0) -> List[Dict[str, Any]]:
    """Normalize line items.

    Each item is stored as:
        {description, hsn_sac, quantity, unit_price, amount, gst_rate}

    hsn_sac (HSN code for goods / SAC for services) is optional but
    required at GSTR-1 export time, so we surface it now. gst_rate
    defaults to the business's default_gst_rate (typically 18%) when
    omitted, so a no-frills invoice still computes GST correctly."""
    from api.gst import SUPPORTED_GST_RATES

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

        # GST rate. Accept missing as "use business default"; reject any
        # value that's not on the supported list (5/12/18/28 + 0/0.25/3).
        rate_raw = it.get("gst_rate")
        if rate_raw is None or rate_raw == "":
            gst_rate = float(default_gst_rate or 0)
        else:
            try:
                gst_rate = float(rate_raw)
            except (TypeError, ValueError):
                raise HTTPException(400, f"Line item {idx} has invalid gst_rate")
        if gst_rate not in SUPPORTED_GST_RATES:
            raise HTTPException(
                400,
                f"Line item {idx} gst_rate {gst_rate} is not a valid GST slab "
                f"(use one of {SUPPORTED_GST_RATES})",
            )

        hsn_sac = (it.get("hsn_sac") or "").strip()
        if len(hsn_sac) > 20:
            raise HTTPException(400, f"Line item {idx} hsn_sac too long")

        amount = round(qty * price, 2)
        normalized.append({
            "description": desc,
            "hsn_sac": hsn_sac,
            "quantity": qty,
            "unit_price": price,
            "amount": amount,
            "gst_rate": gst_rate,
        })
    return normalized


def _compute_totals(
    line_items: List[Dict],
    supplier_state_code: str = "",
    customer_state_code: str = "",
) -> Dict[str, Any]:
    """Run the full GST split. Used by both create_invoice + update.

    Returns the rich shape that maps onto the new DB columns:
        subtotal, igst_amount, cgst_amount, sgst_amount, tax_amount,
        total, items_with_tax, place_of_supply, is_inter_state.
    """
    from api.gst import compute_gst
    g = compute_gst(line_items, supplier_state_code, customer_state_code)
    return {
        "subtotal":     g["subtotal"],
        "igst_amount":  g["igst"],
        "cgst_amount":  g["cgst"],
        "sgst_amount":  g["sgst"],
        "tax_amount":   g["tax_total"],
        "total":        g["total"],
        "items_with_tax": g["items_with_tax"],
        "place_of_supply": customer_state_code or supplier_state_code or "",
        "is_inter_state": g["is_inter_state"],
    }


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

    # ── Resolve supplier (us) + customer state for GST split ────────────
    # Supplier state comes from the business profile; customer state
    # comes from the linked contact / company or from explicit fields
    # in the body. If we can't resolve either, intra-state CGST+SGST
    # is assumed (the safe default for a single-state SMB).
    from api.businesses import get_business
    biz = get_business(business_id) or {}
    supplier_state = (biz.get("state_code") or "").strip()
    default_gst_rate = float(biz.get("default_gst_rate") or 18)
    customer_state = (data.get("customer_state_code") or "").strip()

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
        if not customer_state:
            customer_state = (ct.get("state_code") or "").strip()

    if not customer_name:
        raise HTTPException(400, "Either customer_name, customer_company_id, or customer_contact_id is required")

    line_items = _validate_line_items(
        data.get("line_items", []),
        default_gst_rate=default_gst_rate,
    )
    totals = _compute_totals(line_items, supplier_state, customer_state)

    # tax_pct legacy field: keep populating it as the dominant rate (the
    # single GST slab when all items share one) so old readers still
    # see something sensible. Mixed-rate invoices store 0 here.
    rates_used = {it["gst_rate"] for it in line_items}
    tax_pct = float(next(iter(rates_used))) if len(rates_used) == 1 else 0.0

    # ── UPI deep-link, if the business has a VPA configured ─────────────
    upi_link = ""
    vpa = (biz.get("upi_vpa") or "").strip()
    if vpa:
        try:
            from api.gst import build_upi_link
            upi_link = build_upi_link(
                vpa=vpa,
                payee_name=biz.get("name") or "Payee",
                amount_inr=totals["total"],
                invoice_ref="",  # filled in after we know the number
            )
        except Exception as e:
            logger.debug(f"[invoices] UPI link build failed: {e}")

    status = data.get("status", "draft")
    if status not in STATUSES:
        raise HTTPException(400, f"Invalid status. Must be one of: {', '.join(STATUSES)}")

    issue = _validate_date(data.get("issue_date"), "issue_date") or date.today().isoformat()
    due = _validate_date(data.get("due_date"), "due_date")

    currency = _validate_text(data.get("currency", "INR"), "Currency", 8) or "INR"

    recurrence = (data.get("recurrence") or "none").strip().lower()
    if recurrence not in INVOICE_RECURRENCES:
        raise HTTPException(400, f"Invalid recurrence. Must be one of: {', '.join(INVOICE_RECURRENCES)}")
    recurrence_parent_id = data.get("recurrence_parent_id") or None

    iid = f"inv-{uuid.uuid4().hex[:10]}"
    number = _next_number(business_id)

    # Re-render the UPI link now that we know the number, so the QR
    # carries the invoice ref the customer's bank statement will show.
    if vpa:
        try:
            from api.gst import build_upi_link
            upi_link = build_upi_link(
                vpa=vpa,
                payee_name=biz.get("name") or "Payee",
                amount_inr=totals["total"],
                invoice_ref=number,
            )
        except Exception:
            pass

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
        totals["igst_amount"], totals["cgst_amount"], totals["sgst_amount"],
        totals["place_of_supply"], upi_link,
    )
    conn = _get_conn()
    try:
        conn.execute(
            f"INSERT INTO {INVOICES_TABLE} "
            f"(id, business_id, number, status, customer_company_id, customer_contact_id, "
            f"customer_name, customer_email, customer_address, currency, issue_date, due_date, "
            f"notes, line_items, subtotal, tax_pct, tax_amount, total, pdf_path, paid_at, "
            f"created_at, updated_at, created_by, recurrence, recurrence_parent_id, "
            f"igst_amount, cgst_amount, sgst_amount, place_of_supply, upi_link) "
            f"VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", row,
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
    # tax_pct stays editable for backward-compat but the value gets
    # overwritten on recompute; customer_state_code is the new lever
    # for changing place-of-supply (and thus the IGST vs CGST+SGST split).
    allowed = {"customer_name", "customer_email", "customer_address",
               "currency", "issue_date", "due_date", "notes",
               "line_items", "tax_pct", "status", "recurrence",
               "customer_state_code"}
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

    # Recompute the GST split whenever line items or customer-state
    # change. Customer-state can change because the invoice was
    # re-linked to a contact in a different state (B2B reassignment).
    from api.businesses import get_business
    biz = get_business(business_id) or {}
    supplier_state = (biz.get("state_code") or "").strip()
    default_gst_rate = float(biz.get("default_gst_rate") or 18)

    if "line_items" in fields:
        fields["line_items"] = _validate_line_items(
            fields["line_items"], default_gst_rate=default_gst_rate,
        )

    recompute = "line_items" in fields or "customer_state_code" in fields
    if recompute:
        items = fields.get("line_items", current["line_items"])
        customer_state = (
            fields.get("customer_state_code")
            or current.get("place_of_supply", "")
        ).strip()
        totals = _compute_totals(items, supplier_state, customer_state)
        fields["subtotal"]        = totals["subtotal"]
        fields["tax_amount"]      = totals["tax_amount"]
        fields["total"]           = totals["total"]
        fields["igst_amount"]     = totals["igst_amount"]
        fields["cgst_amount"]     = totals["cgst_amount"]
        fields["sgst_amount"]     = totals["sgst_amount"]
        fields["place_of_supply"] = totals["place_of_supply"]
        # Refresh the legacy tax_pct (kept for backward-compat consumers).
        rates = {it["gst_rate"] for it in items}
        fields["tax_pct"] = float(next(iter(rates))) if len(rates) == 1 else 0.0

        # Refresh UPI link with the new total.
        vpa = (biz.get("upi_vpa") or "").strip()
        if vpa:
            try:
                from api.gst import build_upi_link
                fields["upi_link"] = build_upi_link(
                    vpa=vpa,
                    payee_name=biz.get("name") or "Payee",
                    amount_inr=totals["total"],
                    invoice_ref=current.get("number", ""),
                )
            except Exception as e:
                logger.debug(f"[invoices] UPI link refresh failed: {e}")

    # Status transitions
    extra_sets = []
    extra_params: list = []
    if fields.get("status") == "paid":
        extra_sets.append("paid_at = ?")
        extra_params.append(_now())
    elif "status" in fields and fields["status"] != "paid":
        extra_sets.append("paid_at = NULL")

    # customer_state_code is a computation input, not a stored column —
    # it gets reflected into place_of_supply by _compute_totals above.
    # Strip it before we hand the dict to SQL.
    fields.pop("customer_state_code", None)

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
        "currency": src.get("currency", "INR"),
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
    """Render the invoice to PDF and return the file path.

    Layout:
      Header (INVOICE title + number)
      From (business name / GSTIN / state) | Bill to (customer / GSTIN)
      Line items table — with HSN/SAC + GST rate per item
      Tax breakdown — IGST or CGST+SGST depending on place of supply
      Pay-now block — UPI QR + handle + tap-to-pay link
      Notes
      Footer
    """
    inv = get_invoice(business_id, invoice_id)
    INVOICE_DIR.mkdir(parents=True, exist_ok=True)

    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image,
    )
    from reportlab.lib.utils import ImageReader
    import io as _io

    # Pull the business profile for GSTIN / state / UPI VPA — these
    # populate the new sections of the PDF.
    from api.businesses import get_business
    biz = get_business(business_id) or {}
    biz_gstin = (biz.get("gstin") or "").strip()
    biz_state = (biz.get("state_code") or "").strip()
    biz_vpa   = (biz.get("upi_vpa") or "").strip()

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
        [Paragraph("<b>TAX INVOICE</b>" if biz_gstin else "<b>INVOICE</b>", title_style),
         Paragraph(f"<b>#{inv['number']}</b><br/><font size=9 color='#64748b'>"
                   f"Issued: {inv['issue_date'] or ''}<br/>Due: {inv['due_date'] or '-'}</font>", body)],
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
    from api.gst import state_name as _state_name
    from_lines = [f"<b>{business_name or biz.get('name') or 'Your business'}</b>"]
    if biz_gstin:
        from_lines.append(f"GSTIN: {biz_gstin}")
    if biz_state:
        from_lines.append(f"State: {_state_name(biz_state)} ({biz_state})")
    from_block = "<br/>".join(from_lines)

    to_lines = [f"<b>Bill to</b>", inv['customer_name']]
    if inv.get("customer_email"):
        to_lines.append(inv['customer_email'])
    if inv.get("customer_address"):
        to_lines.extend(inv['customer_address'].split("\n"))
    pos = (inv.get("place_of_supply") or "").strip()
    if pos:
        to_lines.append(f"Place of supply: {_state_name(pos)} ({pos})")
    to_block = "<br/>".join(to_lines)

    addr = Table([[Paragraph(from_block, body), Paragraph(to_block, body)]],
                 colWidths=[8.5 * cm, 8.5 * cm])
    addr.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(addr)
    story.append(Spacer(1, 0.6 * cm))

    # Line items table — now with HSN/SAC + per-line GST
    currency = inv.get("currency", "INR")
    has_gst = any(float(it.get("gst_rate", 0) or 0) > 0 for it in inv["line_items"])
    if has_gst:
        header_row = ["Description", "HSN/SAC", "Qty", f"Unit ({currency})", "GST %", f"Amount ({currency})"]
        col_widths = [6.5 * cm, 2.0 * cm, 1.4 * cm, 2.5 * cm, 1.4 * cm, 3.0 * cm]
    else:
        header_row = ["Description", "Qty", f"Unit ({currency})", f"Amount ({currency})"]
        col_widths = [9.5 * cm, 1.8 * cm, 3 * cm, 3 * cm]
    rows = [header_row]
    for it in inv["line_items"]:
        if has_gst:
            rows.append([
                Paragraph(it["description"], body),
                it.get("hsn_sac", "") or "-",
                f"{it['quantity']:g}",
                f"{it['unit_price']:,.2f}",
                f"{float(it.get('gst_rate', 0) or 0):g}%",
                f"{it['amount']:,.2f}",
            ])
        else:
            rows.append([
                Paragraph(it["description"], body),
                f"{it['quantity']:g}",
                f"{it['unit_price']:,.2f}",
                f"{it['amount']:,.2f}",
            ])
    items_table = Table(rows, colWidths=col_widths)
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

    # Totals block — IGST or CGST+SGST depending on the split actually
    # stored. Falls back to a single 'Tax' row if no GST split present
    # (e.g. legacy invoices or non-INR currency).
    igst = float(inv.get("igst_amount") or 0)
    cgst = float(inv.get("cgst_amount") or 0)
    sgst = float(inv.get("sgst_amount") or 0)
    totals_rows = [["Subtotal", f"{inv['subtotal']:,.2f} {currency}"]]
    if igst > 0:
        totals_rows.append(["IGST", f"{igst:,.2f} {currency}"])
    if cgst > 0 or sgst > 0:
        totals_rows.append(["CGST", f"{cgst:,.2f} {currency}"])
        totals_rows.append(["SGST", f"{sgst:,.2f} {currency}"])
    if not (igst or cgst or sgst) and float(inv.get("tax_amount") or 0):
        totals_rows.append([f"Tax ({inv['tax_pct']:g}%)", f"{inv['tax_amount']:,.2f} {currency}"])
    totals_rows.append(["Total", f"{inv['total']:,.2f} {currency}"])

    totals_table = Table(totals_rows, colWidths=[3 * cm, 3.2 * cm], hAlign="RIGHT")
    n = len(totals_rows)
    totals_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "RIGHT"),
        ("FONTSIZE", (0, 0), (-1, n - 2), 9),
        ("FONTSIZE", (0, n - 1), (-1, n - 1), 11),
        ("FONTNAME", (0, n - 1), (-1, n - 1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, n - 1), (-1, n - 1), ACCENT),
        ("LINEABOVE", (0, n - 1), (-1, n - 1), 1, ACCENT),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(totals_table)
    story.append(Spacer(1, 0.6 * cm))

    # UPI pay-now block — QR + handle + tappable link. Only renders
    # when the business has a VPA configured AND we have a real
    # upi_link stored. Skipped on $0 invoices.
    upi_link = (inv.get("upi_link") or "").strip()
    if upi_link and float(inv.get("total") or 0) > 0 and biz_vpa:
        try:
            from api.gst import build_upi_qr_png
            qr_png = build_upi_qr_png(upi_link, size_px=320)
            qr_img = Image(_io.BytesIO(qr_png), width=3.2 * cm, height=3.2 * cm)
            pay_lines = [
                "<b>Pay by UPI</b>",
                f"Scan with any UPI app (GPay, PhonePe, Paytm, BHIM)",
                f"or send <b>{currency} {inv['total']:,.2f}</b> to:",
                f"<font color='#1e3a5f' size=11><b>{biz_vpa}</b></font>",
                f"<font size=8 color='#64748b'>Mention <b>{inv['number']}</b> "
                f"in the UPI note so we can match the payment.</font>",
            ]
            pay_block = Paragraph("<br/>".join(pay_lines), body)
            pay_table = Table(
                [[qr_img, pay_block]],
                colWidths=[3.6 * cm, 13.4 * cm],
            )
            pay_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#eef2ff")),
                ("LEFTPADDING", (0, 0), (-1, -1), 12),
                ("RIGHTPADDING", (0, 0), (-1, -1), 12),
                ("TOPPADDING", (0, 0), (-1, -1), 12),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 12),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c7d2fe")),
            ]))
            story.append(pay_table)
            story.append(Spacer(1, 0.4 * cm))
        except Exception as e:
            logger.warning(f"[invoices.render_pdf] UPI block failed: {e}")

    # Notes
    if inv.get("notes"):
        story.append(Paragraph("<b>Notes</b>", h2))
        story.append(Paragraph(inv["notes"].replace("\n", "<br/>"), body))
        story.append(Spacer(1, 0.4 * cm))

    # Footer
    story.append(HRFlowable(color=colors.HexColor("#cbd5e1"), thickness=0.5))
    story.append(Spacer(1, 0.2 * cm))
    footer = (
        f"Generated by NexusAgent  "
        f"{datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )
    if biz_gstin:
        footer += f"  - GSTIN {biz_gstin}"
    story.append(Paragraph(footer, small))

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
