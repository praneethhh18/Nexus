"""
Saved queries + templates router (2.7).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(prefix="/api/saved-queries", tags=["saved-queries"])


@router.get("")
def saved_queries_list(ctx: dict = Depends(get_current_context)):
    from api import saved_queries
    return saved_queries.list_queries(ctx["business_id"])


@router.post("")
def saved_queries_create(body: dict, ctx: dict = Depends(get_current_context)):
    from api import saved_queries
    try:
        return saved_queries.create_query(ctx["business_id"], body)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/templates")
def saved_queries_templates(ctx: dict = Depends(get_current_context)):
    from api import saved_queries
    return saved_queries.list_templates()


@router.post("/from-template")
def saved_queries_from_template(body: dict, ctx: dict = Depends(get_current_context)):
    from api import saved_queries
    try:
        return saved_queries.create_from_template(
            ctx["business_id"], body.get("template_key") or "",
        )
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.patch("/{query_id}")
def saved_queries_update(query_id: str, body: dict,
                         ctx: dict = Depends(get_current_context)):
    from api import saved_queries
    try:
        return saved_queries.update_query(ctx["business_id"], query_id, body)
    except KeyError:
        raise HTTPException(404, "Saved query not found")
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/{query_id}")
def saved_queries_delete(query_id: str, ctx: dict = Depends(get_current_context)):
    from api import saved_queries
    saved_queries.delete_query(ctx["business_id"], query_id)
    return {"ok": True}


@router.post("/{query_id}/record-run")
def saved_queries_record_run(query_id: str, ctx: dict = Depends(get_current_context)):
    """Called by the SQL runner after a saved query is executed."""
    from api import saved_queries
    saved_queries.record_run(ctx["business_id"], query_id)
    return {"ok": True}
