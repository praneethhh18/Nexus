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
