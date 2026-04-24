"""
Tags router — universal tags for any record type + full workspace export.
"""
from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response

from api.auth import get_current_context

router = APIRouter(tags=["tags"])


# ── Tag CRUD ───────────────────────────────────────────────────────────────
@router.get("/api/tags")
def tags_list_all(ctx: dict = Depends(get_current_context)):
    """Every tag in the current business, with usage counts."""
    from api import tags as _tags
    return _tags.list_tags(ctx["business_id"])


@router.post("/api/tags")
def tags_create(body: dict, ctx: dict = Depends(get_current_context)):
    """Create a tag (or return the existing one with the same name)."""
    from api import tags as _tags
    try:
        return _tags.create_tag(
            ctx["business_id"],
            name=body.get("name", ""),
            color=body.get("color"),
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/api/tags/{tag_id}")
def tags_delete(tag_id: str, ctx: dict = Depends(get_current_context)):
    from api import tags as _tags
    _tags.delete_tag(ctx["business_id"], tag_id)
    return {"ok": True}


@router.get("/api/tags/for/{entity_type}/{entity_id}")
def tags_for_entity(entity_type: str, entity_id: str,
                    ctx: dict = Depends(get_current_context)):
    from api import tags as _tags
    try:
        return _tags.tags_for(ctx["business_id"], entity_type, entity_id)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.put("/api/tags/for/{entity_type}/{entity_id}")
def tags_set_for_entity(entity_type: str, entity_id: str, body: dict,
                        ctx: dict = Depends(get_current_context)):
    """Replace the entity's tags with `tag_ids`."""
    from api import tags as _tags
    tag_ids = body.get("tag_ids") or []
    try:
        return _tags.set_tags(ctx["business_id"], entity_type, entity_id, tag_ids)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/api/tags/bulk-for/{entity_type}")
def tags_bulk_for(entity_type: str, body: dict,
                  ctx: dict = Depends(get_current_context)):
    """Fetch tags for many entities at once — used by list pages."""
    from api import tags as _tags
    ids = body.get("ids") or []
    try:
        return _tags.bulk_tags_for(ctx["business_id"], entity_type, ids)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ── Workspace data export (lives alongside tags because it references
# the tag tables + every other tenant table) ───────────────────────────────
@router.get("/api/export/all")
def export_all(ctx: dict = Depends(get_current_context)):
    """Bundle every business-scoped table into a ZIP. Owner/admin only."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can export the full workspace")
    from api import data_export
    blob = data_export.build_export_zip(ctx["business_id"])
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return Response(
        content=blob,
        media_type="application/zip",
        headers={
            "Content-Disposition": f'attachment; filename="nexusagent-export-{ts}.zip"',
        },
    )
