"""
AI suggestions router — passive per-record nudges (2.5).
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(prefix="/api/suggestions", tags=["suggestions"])


@router.get("/{entity_type}/{entity_id}")
def suggestions_for_entity(entity_type: str, entity_id: str,
                           ctx: dict = Depends(get_current_context)):
    """Passive per-record nudges (follow-up overdue, client pays late, etc)."""
    from api import suggestions
    try:
        return {"suggestions": suggestions.for_entity(
            ctx["business_id"], entity_type, entity_id,
        )}
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/{suggestion_id}/dismiss")
def suggestions_dismiss(suggestion_id: str,
                        ctx: dict = Depends(get_current_context)):
    """Dismiss a suggestion — it stops surfacing on the related record."""
    from api import suggestions
    suggestions.dismiss(ctx["business_id"], suggestion_id)
    return {"ok": True}
