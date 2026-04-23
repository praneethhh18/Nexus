"""CRM tools — contacts, companies, deals, interactions."""
from __future__ import annotations

from typing import Any, Dict

from agents.tool_registry import register_tool
from api import crm as _crm


# ── Contacts ─────────────────────────────────────────────────────────────────
def _find_contacts(ctx, args):
    return _crm.list_contacts(
        ctx["business_id"],
        search=args.get("search"),
        company_id=args.get("company_id"),
        limit=int(args.get("limit", 20)),
    )


register_tool(
    name="find_contacts",
    description=(
        "Search contacts in the current business's CRM. Returns a list of "
        "contacts matching the search string in name / email / tags. Use this "
        "before create_contact to avoid duplicates."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "search": {"type": "string", "description": "Name, email, or tag to search"},
            "company_id": {"type": "string", "description": "Optional — filter by company id"},
            "limit": {"type": "integer", "default": 20},
        },
    },
    handler=_find_contacts,
)


def _create_contact(ctx, args):
    return _crm.create_contact(ctx["business_id"], ctx["user_id"], args)


register_tool(
    name="create_contact",
    description=(
        "Create a new contact in the CRM. Requires at least first_name or last_name. "
        "Pass company_id if they're at a known company."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "title": {"type": "string", "description": "Job title"},
            "company_id": {"type": "string"},
            "tags": {"type": "string", "description": "Comma-separated tags"},
            "notes": {"type": "string"},
        },
    },
    handler=_create_contact,
    summary_fn=lambda a: f"Add contact: {a.get('first_name','')} {a.get('last_name','')} <{a.get('email','')}>",
)


def _update_contact(ctx, args):
    contact_id = args.pop("contact_id", None)
    if not contact_id:
        raise ValueError("contact_id is required")
    return _crm.update_contact(ctx["business_id"], contact_id, args)


register_tool(
    name="update_contact",
    description="Update fields on an existing contact. Pass contact_id and the fields to change.",
    input_schema={
        "type": "object",
        "properties": {
            "contact_id": {"type": "string"},
            "first_name": {"type": "string"},
            "last_name": {"type": "string"},
            "email": {"type": "string"},
            "phone": {"type": "string"},
            "title": {"type": "string"},
            "company_id": {"type": "string"},
            "tags": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["contact_id"],
    },
    handler=_update_contact,
    summary_fn=lambda a: f"Update contact {a.get('contact_id')}",
)


def _delete_contact(ctx, args):
    _crm.delete_contact(ctx["business_id"], args["contact_id"])
    return {"ok": True}


register_tool(
    name="delete_contact",
    description="Delete a contact. Detaches from deals/interactions. Requires approval.",
    input_schema={
        "type": "object",
        "properties": {"contact_id": {"type": "string"}},
        "required": ["contact_id"],
    },
    handler=_delete_contact,
    summary_fn=lambda a: f"DELETE contact {a.get('contact_id')}",
)


# ── Companies ────────────────────────────────────────────────────────────────
def _find_companies(ctx, args):
    return _crm.list_companies(
        ctx["business_id"],
        search=args.get("search"),
        limit=int(args.get("limit", 20)),
    )


register_tool(
    name="find_companies",
    description="Search companies in the CRM.",
    input_schema={
        "type": "object",
        "properties": {
            "search": {"type": "string"},
            "limit": {"type": "integer", "default": 20},
        },
    },
    handler=_find_companies,
)


def _create_company(ctx, args):
    return _crm.create_company(ctx["business_id"], ctx["user_id"], args)


register_tool(
    name="create_company",
    description="Create a company record. Name is required.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "industry": {"type": "string"},
            "website": {"type": "string"},
            "size": {"type": "string"},
            "tags": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["name"],
    },
    handler=_create_company,
    summary_fn=lambda a: f"Add company: {a.get('name')}",
)


def _update_company(ctx, args):
    cid = args.pop("company_id")
    return _crm.update_company(ctx["business_id"], cid, args)


register_tool(
    name="update_company",
    description="Update a company record.",
    input_schema={
        "type": "object",
        "properties": {
            "company_id": {"type": "string"},
            "name": {"type": "string"},
            "industry": {"type": "string"},
            "website": {"type": "string"},
            "size": {"type": "string"},
            "tags": {"type": "string"},
            "notes": {"type": "string"},
        },
        "required": ["company_id"],
    },
    handler=_update_company,
    summary_fn=lambda a: f"Update company {a.get('company_id')}",
)


def _delete_company(ctx, args):
    _crm.delete_company(ctx["business_id"], args["company_id"])
    return {"ok": True}


register_tool(
    name="delete_company",
    description="Delete a company (detaches contacts/deals). Requires approval.",
    input_schema={
        "type": "object",
        "properties": {"company_id": {"type": "string"}},
        "required": ["company_id"],
    },
    handler=_delete_company,
    summary_fn=lambda a: f"DELETE company {a.get('company_id')}",
)


# ── Deals ────────────────────────────────────────────────────────────────────
def _find_deals(ctx, args):
    return _crm.list_deals(
        ctx["business_id"],
        stage=args.get("stage"),
        search=args.get("search"),
        limit=int(args.get("limit", 50)),
    )


register_tool(
    name="find_deals",
    description=(
        "List deals in the pipeline. Filter by stage (lead|qualified|proposal|"
        "negotiation|won|lost) or search by name/notes."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "stage": {"type": "string", "enum": ["lead", "qualified", "proposal", "negotiation", "won", "lost"]},
            "search": {"type": "string"},
            "limit": {"type": "integer", "default": 50},
        },
    },
    handler=_find_deals,
)


def _create_deal(ctx, args):
    return _crm.create_deal(ctx["business_id"], ctx["user_id"], args)


register_tool(
    name="create_deal",
    description="Create a new deal in the pipeline.",
    input_schema={
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "value": {"type": "number"},
            "currency": {"type": "string", "default": "USD"},
            "stage": {"type": "string", "enum": ["lead", "qualified", "proposal", "negotiation", "won", "lost"], "default": "lead"},
            "probability_pct": {"type": "integer", "default": 20},
            "contact_id": {"type": "string"},
            "company_id": {"type": "string"},
            "notes": {"type": "string"},
            "expected_close": {"type": "string", "description": "YYYY-MM-DD"},
        },
        "required": ["name"],
    },
    handler=_create_deal,
    summary_fn=lambda a: f"Add deal: {a.get('name')} ({a.get('value', 0)} {a.get('currency', 'USD')})",
)


def _update_deal(ctx, args):
    did = args.pop("deal_id")
    return _crm.update_deal(ctx["business_id"], did, args)


register_tool(
    name="update_deal",
    description=(
        "Update a deal — change stage, value, probability, notes, close date. "
        "Useful for moving deals through the pipeline."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "deal_id": {"type": "string"},
            "name": {"type": "string"},
            "value": {"type": "number"},
            "currency": {"type": "string"},
            "stage": {"type": "string", "enum": ["lead", "qualified", "proposal", "negotiation", "won", "lost"]},
            "probability_pct": {"type": "integer"},
            "contact_id": {"type": "string"},
            "company_id": {"type": "string"},
            "notes": {"type": "string"},
            "expected_close": {"type": "string"},
        },
        "required": ["deal_id"],
    },
    handler=_update_deal,
    summary_fn=lambda a: f"Update deal {a.get('deal_id')} — " + ", ".join(
        f"{k}={v}" for k, v in a.items() if k != "deal_id"
    ),
)


def _delete_deal(ctx, args):
    _crm.delete_deal(ctx["business_id"], args["deal_id"])
    return {"ok": True}


register_tool(
    name="delete_deal",
    description="Delete a deal. Requires approval.",
    input_schema={
        "type": "object",
        "properties": {"deal_id": {"type": "string"}},
        "required": ["deal_id"],
    },
    handler=_delete_deal,
    summary_fn=lambda a: f"DELETE deal {a.get('deal_id')}",
)


def _pipeline_stats(ctx, args):
    return _crm.deal_pipeline_stats(ctx["business_id"])


register_tool(
    name="pipeline_stats",
    description="Get the deal pipeline breakdown by stage (counts + total value).",
    input_schema={"type": "object", "properties": {}},
    handler=_pipeline_stats,
)


# ── Interactions ─────────────────────────────────────────────────────────────
def _log_interaction(ctx, args):
    return _crm.create_interaction(ctx["business_id"], ctx["user_id"], args)


register_tool(
    name="log_interaction",
    description=(
        "Log an interaction (call, email, meeting, note) attached to a contact, "
        "company, or deal. Use after a real-world event."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "type": {"type": "string", "enum": ["call", "email", "meeting", "note"]},
            "subject": {"type": "string"},
            "summary": {"type": "string"},
            "contact_id": {"type": "string"},
            "company_id": {"type": "string"},
            "deal_id": {"type": "string"},
            "occurred_at": {"type": "string", "description": "ISO timestamp; defaults to now"},
        },
        "required": ["type", "subject"],
    },
    handler=_log_interaction,
    summary_fn=lambda a: f"Log {a.get('type')}: {a.get('subject', '')[:60]}",
)


def _list_interactions(ctx, args):
    return _crm.list_interactions(
        ctx["business_id"],
        contact_id=args.get("contact_id"),
        company_id=args.get("company_id"),
        deal_id=args.get("deal_id"),
        limit=int(args.get("limit", 50)),
    )


register_tool(
    name="list_interactions",
    description="Fetch past interactions for a contact, company, or deal.",
    input_schema={
        "type": "object",
        "properties": {
            "contact_id": {"type": "string"},
            "company_id": {"type": "string"},
            "deal_id": {"type": "string"},
            "limit": {"type": "integer", "default": 50},
        },
    },
    handler=_list_interactions,
)
