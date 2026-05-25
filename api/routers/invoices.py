"""Invoices router — CRUD, summary, bulk ops, PDF render + download."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse

from api import invoices as _inv
from api.auth import get_current_context

router = APIRouter(tags=["invoices"])


@router.get("/api/invoices")
def list_invoices_api(
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = 200,
    ctx: dict = Depends(get_current_context),
):
    return _inv.list_invoices(ctx["business_id"], status=status, search=search, limit=limit)


@router.post("/api/invoices")
def create_invoice_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _inv.create_invoice(ctx["business_id"], ctx["user"]["id"], body)


@router.get("/api/invoices/summary")
def invoice_summary_api(ctx: dict = Depends(get_current_context)):
    return _inv.invoice_summary(ctx["business_id"])


@router.get("/api/invoices/{invoice_id}")
def get_invoice_api(invoice_id: str, ctx: dict = Depends(get_current_context)):
    return _inv.get_invoice(ctx["business_id"], invoice_id)


@router.patch("/api/invoices/{invoice_id}")
def update_invoice_api(invoice_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _inv.update_invoice(ctx["business_id"], invoice_id, body)


@router.delete("/api/invoices/{invoice_id}")
def delete_invoice_api(invoice_id: str, ctx: dict = Depends(get_current_context)):
    _inv.delete_invoice(ctx["business_id"], invoice_id)
    return {"ok": True}


@router.post("/api/invoices/bulk-delete")
def bulk_delete_invoices_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    return {"deleted": _inv.bulk_delete_invoices(ctx["business_id"], ids)}


@router.post("/api/invoices/bulk-status")
def bulk_invoice_status_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    status = body.get("status") or ""
    return {"updated": _inv.bulk_update_invoice_status(ctx["business_id"], ids, status)}


@router.post("/api/invoices/{invoice_id}/render")
def render_invoice_pdf(invoice_id: str, ctx: dict = Depends(get_current_context)):
    from api.businesses import get_business
    biz = get_business(ctx["business_id"])
    path = _inv.render_pdf(ctx["business_id"], invoice_id, business_name=biz["name"] if biz else "")
    filename = Path(path).name
    return {"path": path, "filename": filename, "download_url": f"/api/invoices/{invoice_id}/pdf"}


@router.get("/api/invoices/{invoice_id}/pdf")
def download_invoice_pdf(invoice_id: str, ctx: dict = Depends(get_current_context)):
    inv = _inv.get_invoice(ctx["business_id"], invoice_id)
    pdf_path = inv.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        from api.businesses import get_business
        biz = get_business(ctx["business_id"])
        pdf_path = _inv.render_pdf(ctx["business_id"], invoice_id, business_name=biz["name"] if biz else "")
    filename = Path(pdf_path).name
    return FileResponse(str(pdf_path), filename=filename, media_type="application/pdf")


# ── Mark-as-paid (manual reconciliation against UPI/bank) ───────────────────
# An SMB owner sees a UPI SMS land on their phone after the customer
# scans the invoice QR. They tap "Mark paid" here to close the loop;
# we stamp paid_at + record the payment reference for the GSTR-1
# export. Future: a UPI provider webhook can fire the same logic.
@router.post("/api/invoices/{invoice_id}/mark-paid")
def mark_invoice_paid(invoice_id: str, body: dict = None,
                      ctx: dict = Depends(get_current_context)):
    body = body or {}
    payment_ref = (body.get("payment_ref") or "").strip()[:200]
    method = (body.get("method") or "upi").strip().lower()
    notes_suffix = (
        f"\n\n[paid via {method}]"
        + (f" ref: {payment_ref}" if payment_ref else "")
    )
    inv = _inv.get_invoice(ctx["business_id"], invoice_id)
    updates = {"status": "paid"}
    if payment_ref or method != "upi":
        # Append-only payment note so we keep prior context (no overwrite).
        existing_notes = (inv.get("notes") or "").rstrip()
        updates["notes"] = (existing_notes + notes_suffix).strip()
    return _inv.update_invoice(ctx["business_id"], invoice_id, updates)


# ── GSTR-1 export (outward-supply summary CSV per month) ───────────────────
# Indian GST filings need a B2B + B2C breakdown per HSN/SAC + rate.
# This is the "give it to your accountant" export — they paste it into
# the official GSTR-1 template. Filters by issue_date month.
@router.get("/api/invoices/export/gstr1")
def export_gstr1(
    month: str,            # 'YYYY-MM'
    ctx: dict = Depends(get_current_context),
):
    from fastapi import HTTPException
    from fastapi.responses import StreamingResponse
    import csv, io as _io, re as _re

    if not _re.match(r"^\d{4}-\d{2}$", month):
        raise HTTPException(400, "month must be 'YYYY-MM'")

    # All invoices in that month that aren't drafts (GSTR-1 only reports
    # outward supplies the customer has been billed for).
    rows = _inv.list_invoices(ctx["business_id"], limit=5000)
    rows = [r for r in rows
            if r.get("status") not in ("draft", "cancelled")
            and (r.get("issue_date") or "").startswith(month)]

    buf = _io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "Invoice number", "Issue date", "Customer", "Place of supply",
        "HSN/SAC", "Description", "Qty", "Unit price", "Taxable value",
        "GST rate", "IGST", "CGST", "SGST", "Total", "Status",
    ])
    for inv in rows:
        items = inv.get("line_items") or []
        # If a single-line invoice, write one row; for multi-line we
        # write one CSV row per item so HSN-level totals are derivable.
        for it in items:
            rate = float(it.get("gst_rate", 0) or 0)
            taxable = float(it.get("amount", 0) or 0)
            tax = round(taxable * rate / 100, 2)
            # Allocate the per-row IGST/CGST/SGST by mirroring the
            # invoice-level split rule.
            is_inter = float(inv.get("igst_amount") or 0) > 0
            igst = tax if is_inter else 0.0
            cgst = round(tax / 2, 2) if not is_inter else 0.0
            sgst = round(tax - cgst, 2) if not is_inter else 0.0
            w.writerow([
                inv.get("number", ""),
                inv.get("issue_date", ""),
                inv.get("customer_name", ""),
                inv.get("place_of_supply", ""),
                it.get("hsn_sac", ""),
                it.get("description", ""),
                it.get("quantity", ""),
                it.get("unit_price", ""),
                taxable,
                f"{rate:g}",
                igst, cgst, sgst,
                round(taxable + tax, 2),
                inv.get("status", ""),
            ])

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition":
                f'attachment; filename="gstr1_{ctx["business_id"]}_{month}.csv"',
        },
    )
