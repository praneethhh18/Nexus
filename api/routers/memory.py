"""
Business-memory CRUD + consolidation. Memory is the long-running notebook
the agent references on every chat — stored locally, never pushed to the
cloud unless the user explicitly asks for a consolidation pass.
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from api.auth import get_current_context
from agents import business_memory as _mem

router = APIRouter(tags=["memory"])


@router.get("/api/memory")
def list_memory_api(search: Optional[str] = None, limit: int = 100,
                    ctx: dict = Depends(get_current_context)):
    return _mem.list_memory(ctx["business_id"], search=search, limit=limit)


@router.post("/api/memory")
def add_memory_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _mem.add_memory(
        ctx["business_id"], ctx["user"]["id"],
        content=body.get("content", ""),
        kind=body.get("kind", "fact"),
        tags=body.get("tags", ""),
        is_pinned=bool(body.get("is_pinned", False)),
    )


@router.patch("/api/memory/{memory_id}")
def update_memory_api(memory_id: str, body: dict,
                      ctx: dict = Depends(get_current_context)):
    return _mem.update_memory(ctx["business_id"], memory_id, body)


@router.delete("/api/memory/{memory_id}")
def delete_memory_api(memory_id: str, ctx: dict = Depends(get_current_context)):
    _mem.delete_memory(ctx["business_id"], memory_id)
    return {"ok": True}


@router.post("/api/memory/consolidate")
def consolidate_memory_api(body: dict = None,
                           ctx: dict = Depends(get_current_context)):
    """Dry-run (apply=false) or apply the consolidation plan for this business."""
    from agents.summarizer import consolidate_business_memory
    body = body or {}
    return consolidate_business_memory(
        ctx["business_id"],
        apply_changes=bool(body.get("apply", False)),
        preserve_pinned=bool(body.get("preserve_pinned", True)),
    )
