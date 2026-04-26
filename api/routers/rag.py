"""
RAG collection + document-expiry endpoints. Lets the user organise their
ingested knowledge into named collections, set expiry dates, find stale
documents, and queue documents for re-ingestion.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["rag"])


@router.get("/api/rag/collections")
def rag_collections_list(ctx: dict = Depends(get_current_context)):
    from api import rag_collections
    return rag_collections.list_collections(ctx["business_id"])


@router.post("/api/rag/collections")
def rag_collections_create(body: dict, ctx: dict = Depends(get_current_context)):
    from api import rag_collections
    try:
        return rag_collections.create_collection(
            ctx["business_id"],
            name=body.get("name", ""),
            description=body.get("description", ""),
            color=body.get("color"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/api/rag/collections/{collection_id}")
def rag_collections_delete(collection_id: str,
                           ctx: dict = Depends(get_current_context)):
    from api import rag_collections
    rag_collections.delete_collection(ctx["business_id"], collection_id)
    return {"ok": True}


@router.put("/api/rag/documents/{document_id}/collection")
def rag_assign_document(document_id: str, body: dict,
                        ctx: dict = Depends(get_current_context)):
    from api import rag_collections
    try:
        rag_collections.assign_document(
            ctx["business_id"], document_id, body.get("collection_id"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@router.put("/api/rag/documents/{document_id}/expiry")
def rag_set_expiry(document_id: str, body: dict,
                   ctx: dict = Depends(get_current_context)):
    from api import rag_collections
    try:
        rag_collections.set_expiry(
            ctx["business_id"], document_id, body.get("expires_at"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"ok": True}


@router.get("/api/rag/documents/stale")
def rag_stale_documents(ctx: dict = Depends(get_current_context)):
    from api import rag_collections
    return {"documents": rag_collections.stale_documents(ctx["business_id"])}


@router.post("/api/rag/documents/{document_id}/reingest")
def rag_reingest_document(document_id: str,
                          ctx: dict = Depends(get_current_context)):
    from api import rag_collections
    try:
        return rag_collections.mark_for_reingest(ctx["business_id"], document_id)
    except KeyError:
        raise HTTPException(404, "Document not found")
