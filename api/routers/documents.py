"""Documents router — proposals, SOW, contracts, offer letters."""
from __future__ import annotations

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from api import documents as _docs
from api.auth import get_current_context
from config.settings import OUTPUTS_DIR

router = APIRouter(tags=["documents"])

ASSETS_DIR = Path(OUTPUTS_DIR) / "documents" / "_assets"
MAX_ASSET_BYTES = 5 * 1024 * 1024   # 5 MB
ALLOWED_IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp"}


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
        logo_path=body.get("logo_path") or None,
        category=body.get("category"),
    )


@router.patch("/api/documents/{document_id}")
def update_document_meta(document_id: str, body: dict,
                         ctx: dict = Depends(get_current_context)):
    """Update document metadata in place — currently just the category bucket
    so users can re-tag a doc after upload without re-generating."""
    new_cat = _docs._validate_category(body.get("category"))
    from config.db import get_conn
    conn = get_conn()
    try:
        cur = conn.execute(
            "UPDATE nexus_documents SET category = ? "
            "WHERE id = ? AND business_id = ?",
            (new_cat, document_id, ctx["business_id"]),
        )
        if cur.rowcount == 0:
            raise HTTPException(404, "Document not found")
        conn.commit()
    finally:
        conn.close()
    return {"ok": True, "category": new_cat}


@router.post("/api/documents/upload-asset")
async def upload_document_asset(
    file: UploadFile = File(...),
    ctx: dict = Depends(get_current_context),
):
    """Upload an image asset (logo, header) for embedding in generated docs.
    Returns the server-side path the /generate call should reference."""
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_IMAGE_EXT:
        raise HTTPException(400, f"Unsupported image format. Use one of: "
                                  f"{', '.join(sorted(ALLOWED_IMAGE_EXT))}")
    buf = bytearray()
    while True:
        chunk = await file.read(1024 * 64)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > MAX_ASSET_BYTES:
            raise HTTPException(413, f"Image too large (max {MAX_ASSET_BYTES // (1024*1024)} MB).")
    biz_assets = ASSETS_DIR / ctx["business_id"]
    biz_assets.mkdir(parents=True, exist_ok=True)
    name = f"{uuid.uuid4().hex[:12]}{ext}"
    out = biz_assets / name
    out.write_bytes(bytes(buf))
    return {"path": str(out), "filename": name}


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
