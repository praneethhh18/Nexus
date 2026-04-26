"""CRM router — companies, contacts, deals, interactions, pipeline, bulk ops."""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends

from api import crm as _crm
from api.auth import get_current_context

router = APIRouter(tags=["crm"])


@router.get("/api/crm/overview")
def crm_overview(ctx: dict = Depends(get_current_context)):
    return _crm.crm_overview(ctx["business_id"])


@router.get("/api/crm/pipeline")
def pipeline_api(ctx: dict = Depends(get_current_context)):
    return _crm.deal_pipeline_stats(ctx["business_id"])


# ── Companies ────────────────────────────────────────────────────────────────
@router.get("/api/crm/companies")
def list_companies_api(search: Optional[str] = None, limit: int = 100,
                       ctx: dict = Depends(get_current_context)):
    return _crm.list_companies(ctx["business_id"], search=search, limit=limit)


@router.post("/api/crm/companies")
def create_company_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_company(ctx["business_id"], ctx["user"]["id"], body)


@router.get("/api/crm/companies/{company_id}")
def get_company_api(company_id: str, ctx: dict = Depends(get_current_context)):
    return _crm.get_company(ctx["business_id"], company_id)


@router.patch("/api/crm/companies/{company_id}")
def update_company_api(company_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.update_company(ctx["business_id"], company_id, body)


@router.delete("/api/crm/companies/{company_id}")
def delete_company_api(company_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_company(ctx["business_id"], company_id)
    return {"ok": True}


@router.post("/api/crm/companies/bulk-delete")
def bulk_delete_companies_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    return {"deleted": _crm.bulk_delete_companies(ctx["business_id"], ids)}


# ── Contacts ─────────────────────────────────────────────────────────────────
@router.get("/api/crm/contacts")
def list_contacts_api(search: Optional[str] = None, company_id: Optional[str] = None,
                      limit: int = 100, ctx: dict = Depends(get_current_context)):
    return _crm.list_contacts(ctx["business_id"], search=search, company_id=company_id, limit=limit)


@router.post("/api/crm/contacts")
def create_contact_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_contact(ctx["business_id"], ctx["user"]["id"], body)


@router.get("/api/crm/contacts/{contact_id}")
def get_contact_api(contact_id: str, ctx: dict = Depends(get_current_context)):
    return _crm.get_contact(ctx["business_id"], contact_id)


@router.patch("/api/crm/contacts/{contact_id}")
def update_contact_api(contact_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.update_contact(ctx["business_id"], contact_id, body)


@router.delete("/api/crm/contacts/{contact_id}")
def delete_contact_api(contact_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_contact(ctx["business_id"], contact_id)
    return {"ok": True}


@router.post("/api/crm/contacts/bulk-delete")
def bulk_delete_contacts_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    return {"deleted": _crm.bulk_delete_contacts(ctx["business_id"], ids)}


# ── Deals ────────────────────────────────────────────────────────────────────
@router.get("/api/crm/deals")
def list_deals_api(stage: Optional[str] = None, search: Optional[str] = None,
                   limit: int = 200, ctx: dict = Depends(get_current_context)):
    return _crm.list_deals(ctx["business_id"], stage=stage, search=search, limit=limit)


@router.post("/api/crm/deals")
def create_deal_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_deal(ctx["business_id"], ctx["user"]["id"], body)


@router.get("/api/crm/deals/{deal_id}")
def get_deal_api(deal_id: str, ctx: dict = Depends(get_current_context)):
    return _crm.get_deal(ctx["business_id"], deal_id)


@router.patch("/api/crm/deals/{deal_id}")
def update_deal_api(deal_id: str, body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.update_deal(ctx["business_id"], deal_id, body)


@router.delete("/api/crm/deals/{deal_id}")
def delete_deal_api(deal_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_deal(ctx["business_id"], deal_id)
    return {"ok": True}


@router.post("/api/crm/deals/bulk-delete")
def bulk_delete_deals_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    return {"deleted": _crm.bulk_delete_deals(ctx["business_id"], ids)}


@router.post("/api/crm/deals/bulk-stage")
def bulk_stage_deals_api(body: dict, ctx: dict = Depends(get_current_context)):
    ids = body.get("ids") or []
    stage = body.get("stage") or ""
    return {"updated": _crm.bulk_update_deal_stage(ctx["business_id"], ids, stage)}


# ── Interactions ─────────────────────────────────────────────────────────────
@router.get("/api/crm/interactions")
def list_interactions_api(contact_id: Optional[str] = None, company_id: Optional[str] = None,
                          deal_id: Optional[str] = None, limit: int = 100,
                          ctx: dict = Depends(get_current_context)):
    return _crm.list_interactions(
        ctx["business_id"],
        contact_id=contact_id, company_id=company_id, deal_id=deal_id, limit=limit,
    )


@router.post("/api/crm/interactions")
def create_interaction_api(body: dict, ctx: dict = Depends(get_current_context)):
    return _crm.create_interaction(ctx["business_id"], ctx["user"]["id"], body)


@router.delete("/api/crm/interactions/{interaction_id}")
def delete_interaction_api(interaction_id: str, ctx: dict = Depends(get_current_context)):
    _crm.delete_interaction(ctx["business_id"], interaction_id)
    return {"ok": True}
