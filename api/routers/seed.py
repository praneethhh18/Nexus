"""
Sample-data seeding for fresh businesses — populates a new tenant with
realistic CRM, tasks, and invoices so users can see the app in action
before importing their own data.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from api.auth import get_current_context

router = APIRouter(tags=["seed"])


@router.post("/api/seed/sample-data")
def seed_sample(ctx: dict = Depends(get_current_context)):
    """Populate the current business with sample companies, contacts, deals,
    tasks, and invoices. Admin/owner only. Refuses if data already exists."""
    if ctx["business_role"] not in ("owner", "admin"):
        raise HTTPException(403, "Only owner/admin can seed sample data")
    from api.seed_data import seed_sample_data
    return seed_sample_data(ctx["business_id"], ctx["user"]["id"])
