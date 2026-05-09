"""Email-templates router — CRUD over /api/email-templates."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api import email_templates as _et
from api.auth import get_current_context

router = APIRouter(tags=["email_templates"])


@router.get("/api/email-templates")
def templates_list(ctx: dict = Depends(get_current_context)):
    return {"templates": _et.list_templates(ctx["business_id"])}


@router.post("/api/email-templates")
def templates_create(body: dict, ctx: dict = Depends(get_current_context)):
    try:
        return _et.create_template(ctx["business_id"], ctx["user"]["id"], body)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.get("/api/email-templates/{template_id}")
def templates_get(template_id: str, ctx: dict = Depends(get_current_context)):
    return _et.get_template(ctx["business_id"], template_id)


@router.patch("/api/email-templates/{template_id}")
def templates_update(template_id: str, body: dict,
                     ctx: dict = Depends(get_current_context)):
    try:
        return _et.update_template(ctx["business_id"], template_id, body)
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.delete("/api/email-templates/{template_id}")
def templates_delete(template_id: str, ctx: dict = Depends(get_current_context)):
    _et.delete_template(ctx["business_id"], template_id)
    return {"ok": True}


@router.post("/api/email-templates/{template_id}/render")
def templates_render(template_id: str, body: dict,
                     ctx: dict = Depends(get_current_context)):
    """Preview a template with variable substitution. Body: {variables: {...}}.
    Doesn't send anything — just returns the rendered subject + body."""
    variables = (body or {}).get("variables") or {}
    return _et.render_template(ctx["business_id"], template_id, variables)
