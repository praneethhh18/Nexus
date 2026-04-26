"""
Research-agent endpoints — generate a structured report on a subject and
optionally save it back to the RAG knowledge base for future retrieval.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["research"])


@router.post("/api/research/structured")
def research_structured(body: dict, ctx: dict = Depends(get_current_context)):
    from agents.research_agent import structured_research
    subject = (body.get("subject") or "").strip()
    if not subject:
        raise HTTPException(400, "subject is required")
    try:
        return structured_research(subject, context=(body.get("context") or ""))
    except ValueError as e:
        raise HTTPException(400, str(e))


@router.post("/api/research/save-to-kb")
def research_save_to_kb(body: dict, ctx: dict = Depends(get_current_context)):
    """Save a structured research report into the RAG knowledge base."""
    from agents.research_agent import save_report_to_kb
    report = body.get("report") or {}
    if not report.get("subject"):
        raise HTTPException(400, "report.subject is required")
    return save_report_to_kb(ctx["business_id"], report)
