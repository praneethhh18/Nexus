"""Documents router — proposals, SOW, contracts, offer letters."""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from api import documents as _docs
from api.auth import get_current_context

router = APIRouter(tags=["documents"])


@router.get("/api/documents/templates")
def list_doc_templates(ctx: dict = Depends(get_current_context)):
    return _docs.list_templates()


@router.get("/api/documents/templates/{template_key}")
def get_doc_template(template_key: str, ctx: dict = Depends(get_current_context)):
    return _docs.get_template(template_key)


@router.get("/api/documents")
def list_documents_api(limit: int = 100, ctx: dict = Depends(get_current_context)):
    return _docs.list_documents(ctx["business_id"], limit=limit)


@router.post("/api/documents/generate")
def generate_document_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _docs.generate_document(
        business_id=ctx["business_id"],
        user_id=ctx["user"]["id"],
        template_key=body.get("template_key", ""),
        title=body.get("title", ""),
        variables=body.get("variables", {}) or {},
        fmt=body.get("format", "docx"),
    )


@router.get("/api/documents/{document_id}")
def get_document_api(document_id: str, ctx: dict = Depends(get_current_context)):
    return _docs.get_document(ctx["business_id"], document_id)


@router.get("/api/documents/{document_id}/download")
def download_document(document_id: str, ctx: dict = Depends(get_current_context)):
    doc = _docs.get_document(ctx["business_id"], document_id)
    path = Path(doc["file_path"])
    if not path.exists():
        raise HTTPException(404, "Document file missing on disk")
    media = "application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
        if doc["format"] == "docx" else "application/pdf"
    return FileResponse(str(path), filename=path.name, media_type=media)


@router.delete("/api/documents/{document_id}")
def delete_document_api(document_id: str, ctx: dict = Depends(get_current_context)):
    _docs.delete_document(ctx["business_id"], document_id)
    return {"ok": True}
