"""CRM tools — contacts, companies, deals, interactions."""
from __future__ import annotations

import re
from typing import Any, Dict, Optional

from agents.tool_registry import register_tool
from api import crm as _crm


# ── Dedup helpers ───────────────────────────────────────────────────────────
# Background: with conversation memory, an agent following multi-turn intent
# ("add Rajesh" → "add his email") still sometimes calls create_contact a
# second time with overlapping details, producing a duplicate. These helpers
# search the CRM before creating so a near-match is updated instead.

def _norm_email(s: Any) -> str:
    return str(s or "").strip().lower()


def _norm_phone(s: Any) -> str:
    """Reduce a phone to digits-only for fuzzy matching across formats."""
    return re.sub(r"\D", "", str(s or ""))


def _norm_name(s: Any) -> str:
    return re.sub(r"\s+", " ", str(s or "").strip()).lower()


def _find_existing_contact(business_id: str, args: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return an existing contact that matches `args`, or None.

    Match precedence (strongest first):
      1. Exact email (case-insensitive)
      2. Exact phone (digits-only)
      3. Exact (first_name + last_name) — case + whitespace-insensitive
      4. First name only when last_name is missing on both sides

    Reads via list_contacts with a `search` filter, so it's bounded by the
    same 100-row cap and tenant scope as any other CRM read.
    """
    email = _norm_email(args.get("email"))
    phone = _norm_phone(args.get("phone"))
    first = _norm_name(args.get("first_name"))
    last  = _norm_name(args.get("last_name"))

    if email:
        # Search by email substring; verify exact match locally.
        for c in _crm.list_contacts(business_id, search=email, limit=20):
            if _norm_email(c.get("email")) == email:
                return c
    if phone:
        # `list_contacts` doesn't index phone; pull a wider set and filter.
        # The search field doesn't search phone either, so do a no-search query.
        for c in _crm.list_contacts(business_id, limit=200):
            if _norm_phone(c.get("phone")) == phone:
                return c
    if first or last:
        # `list_contacts` LIKE-searches first_name OR last_name OR email OR tags
        # individually, so combining "first last" as one search string would
        # never match any single column. Search by whichever name part we have,
        # then verify the full match locally.
        search_term = first or last
        for c in _crm.list_contacts(business_id, search=search_term, limit=200):
            cf = _norm_name(c.get("first_name"))
            cl = _norm_name(c.get("last_name"))
            if first and last:
                if cf == first and cl == last:
                    return c
            elif first and not last:
                # Only match a single-name candidate to avoid swallowing
                # "Rajesh Kumar" when user typed "Rajesh".
                if cf == first and not cl:
                    return c
            elif last and not first:
                if cl == last and not cf:
                    return c
    return None


def _find_existing_company(business_id: str, name: str) -> Optional[Dict[str, Any]]:
    if not name:
        return None
    target = _norm_name(name)
    if not target:
        return None
    # Strip whitespace before passing to LIKE — "%  Acme  %" won't match "Acme".
    for c in _crm.list_companies(business_id, search=target, limit=200):
        if _norm_name(c.get("name")) == target:
            return c
    return None


def _merge_updates(existing: Dict[str, Any], incoming: Dict[str, Any], allowed: set) -> Dict[str, Any]:
    """Return only fields where the incoming value would actually change the
    record AND the existing field is empty or being explicitly updated.

    Rule: if the existing record already has a non-empty value, we DON'T
    overwrite from a create call — the caller has to use update_contact for
    that. This protects against the "create with new details" pattern silently
    rewriting authoritative data.
    """
    out: Dict[str, Any] = {}
    for k, v in incoming.items():
        if k not in allowed:
            continue
        if v is None or (isinstance(v, str) and not v.strip()):
            continue
        cur = existing.get(k)
        cur_str = "" if cur is None else str(cur).strip()
        if not cur_str:
            out[k] = v
    return out


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
    """Search-first create: avoid duplicates by detecting near-matches and
    folding new fields into the existing record. Returns the contact dict
    plus a `_dedup` marker so the LLM can phrase its reply correctly.
    """
    business_id = ctx["business_id"]
    existing = _find_existing_contact(business_id, args)
    if existing:
        allowed = {"first_name", "last_name", "email", "phone", "title",
                   "company_id", "notes", "tags"}
        new_fields = _merge_updates(existing, args, allowed)
        if new_fields:
            updated = _crm.update_contact(business_id, existing["id"], new_fields)
            return {**updated, "_dedup": "merged",
                    "_dedup_msg": f"Found existing contact, updated {sorted(new_fields)}"}
        return {**existing, "_dedup": "duplicate",
                "_dedup_msg": "Contact already exists with these details — no new info to add."}
    return _crm.create_contact(business_id, ctx["user_id"], args)


register_tool(
    name="create_contact",
    description=(
        "Create a new contact in the CRM. Requires at least first_name or last_name. "
        "Pass company_id if they're at a known company. "
        "AUTOMATICALLY DEDUPLICATES: if a contact with matching email, phone, "
        "or full name already exists, this updates the existing record with "
        "any new fields instead of creating a duplicate. The reply will say "
        "whether the contact was 'merged', 'duplicate', or freshly created."
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
    """Search-first create — same pattern as create_contact."""
    business_id = ctx["business_id"]
    existing = _find_existing_company(business_id, args.get("name", ""))
    if existing:
        allowed = {"name", "industry", "website", "size", "tags", "notes"}
        new_fields = _merge_updates(existing, args, allowed)
        if new_fields:
            updated = _crm.update_company(business_id, existing["id"], new_fields)
            return {**updated, "_dedup": "merged",
                    "_dedup_msg": f"Found existing company, updated {sorted(new_fields)}"}
        return {**existing, "_dedup": "duplicate",
                "_dedup_msg": "Company already exists with these details."}
    return _crm.create_company(business_id, ctx["user_id"], args)


register_tool(
    name="create_company",
    description=(
        "Create a company record. Name is required. "
        "AUTOMATICALLY DEDUPLICATES: if a company with the same name "
        "already exists, this updates the existing record instead. "
        "The reply will say 'merged', 'duplicate', or freshly created."
    ),
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
