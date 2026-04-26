"""
Per-entity activity timeline.

Combines tags, tasks, invoices, and tool-call events into one chronological
feed for any record (a contact, deal, company, etc.) — drives the activity
panel on the entity-detail pages.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["activity"])


@router.get("/api/activity/{entity_type}/{entity_id}")
def activity_timeline_api(entity_type: str, entity_id: str, limit: int = 200,
                          ctx: dict = Depends(get_current_context)):
    """Per-record activity timeline — tags, tasks, invoices, tool calls."""
    from api import activity_feed
    try:
        return {"events": activity_feed.timeline(
            ctx["business_id"], entity_type, entity_id, limit=limit,
        )}
    except ValueError as e:
        raise HTTPException(400, str(e))
