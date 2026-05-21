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


@router.post("/api/documents/upload")
async def upload_document_to_kb(
    file: UploadFile = File(...),
    category: str = "other",
    title: str = "",
    ctx: dict = Depends(get_current_context),
):
    """
    Upload a PDF / DOCX / TXT into the workspace's knowledge base.

    Flow:
      1. Save the file under outputs/documents/<biz>/uploads/.
      2. Run ingest_file → chunks (PDF/DOCX/TXT all supported).
      3. Embed the chunks (Bedrock Titan or local Ollama based on settings).
      4. Push to ChromaDB so agents can find them via search_knowledge.
      5. Record the doc in nexus_documents with the chosen category so the
         category filter on search_knowledge can scope to "competitor only"
         (or whichever bucket) at query time.

    Returns the doc id + chunks added so the UI can show a success message.
    """
    import uuid as _uuid
    from datetime import datetime as _dt
    from pathlib import Path as _P
    from config.settings import OUTPUTS_DIR
    from config.db import get_conn

    # Validate file
    ext = _P(file.filename or "").suffix.lower()
    if ext not in {".pdf", ".docx", ".doc", ".txt", ".md"}:
        raise HTTPException(400, "Unsupported file. Use PDF, DOCX, or TXT.")

    # Cap size — knowledge-base ingests can be larger than thumbnails but
    # still need a ceiling so a misclick doesn't OOM the vectoriser.
    MAX_KB_BYTES = 30 * 1024 * 1024
    buf = bytearray()
    while True:
        chunk = await file.read(1024 * 64)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > MAX_KB_BYTES:
            raise HTTPException(413, f"File too large (max {MAX_KB_BYTES // (1024*1024)} MB).")
    if not buf:
        raise HTTPException(400, "Empty file.")

    biz_dir = _P(OUTPUTS_DIR) / "documents" / ctx["business_id"] / "uploads"
    biz_dir.mkdir(parents=True, exist_ok=True)
    name = f"{_uuid.uuid4().hex[:10]}_{file.filename}"
    out_path = biz_dir / name
    out_path.write_bytes(bytes(buf))

    # Parse + embed + add to vector store
    try:
        from rag.ingestion import ingest_file
        from rag.embedder import embed_documents
        from rag.vector_store import add_documents

        chunks = ingest_file(str(out_path))
        if not chunks:
            # Clean up the saved file so we don't accumulate junk on failure.
            try: out_path.unlink()
            except Exception: pass
            raise HTTPException(400,
                "Could not extract text from this file. If it's a scanned PDF, "
                "paste the text into the Extract panel instead.")

        texts = [c.page_content for c in chunks]
        metadatas = []
        for c in chunks:
            meta = dict(c.metadata or {})
            # Tag every chunk with the business + category so the retriever
            # can filter later. The actual category filter currently happens
            # in search_knowledge against nexus_documents, but stamping the
            # metadata too lets us upgrade to vector-side filtering later
            # without a re-ingest.
            meta["business_id"] = ctx["business_id"]
            meta["category"] = _docs._validate_category(category)
            metadatas.append(meta)
        embeddings = embed_documents(texts, sensitive=False)
        added = add_documents(texts, embeddings, metadatas)
    except HTTPException:
        raise
    except Exception as e:
        try: out_path.unlink()
        except Exception: pass
        raise HTTPException(500, f"Ingest failed: {e}")

    # Record in nexus_documents so the UI list + category filter work.
    doc_id = f"doc-{_uuid.uuid4().hex[:10]}"
    now = _dt.now().isoformat()
    safe_title = (title or _P(file.filename or "Untitled").stem)[:200]
    safe_category = _docs._validate_category(category)
    conn = get_conn()
    try:
        conn.execute(
            "INSERT INTO nexus_documents "
            "(id, business_id, template_key, title, format, file_path, variables, "
            " created_at, created_by, category) "
            "VALUES (?, ?, 'uploaded', ?, ?, ?, '{}', ?, ?, ?)",
            (doc_id, ctx["business_id"], safe_title, ext.lstrip("."),
             str(out_path), now, ctx["user"]["id"], safe_category),
        )
        conn.commit()
    finally:
        conn.close()

    return {
        "id": doc_id,
        "title": safe_title,
        "file_path": str(out_path),
        "filename": out_path.name,
        "category": safe_category,
        "chunks_added": int(added or 0),
        "chunk_count": len(chunks),
    }


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
