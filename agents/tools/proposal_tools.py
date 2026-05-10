"""Proposal generation tool — natural-language brief → PDF in seconds.

User in chat / WhatsApp:
    "Generate a proposal for Mehta — 5K flyers at Rs 40 each by Diwali"

Tool flow:
    1. Looks up the named contact in CRM (or accepts contact_id)
    2. Calls api.proposals.generate_proposal() — LLM → spec → ReportLab → PDF
    3. Saves the PDF to data/proposals/<id>.pdf
    4. Returns a `files` array the chat UI auto-renders as a download button

The agent loop already surfaces tool result `files` as download buttons in
chat AND as WhatsApp attachments (existing pattern in agent_loop.py +
notification_tools.send_email).
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger

from agents.tool_registry import register_tool


def _resolve_contact_id(business_id: str, contact_id: str,
                         contact_name: str) -> Optional[str]:
    """If the agent passed a contact_name instead of an id, try to match it."""
    if contact_id:
        return contact_id.strip()
    name = (contact_name or "").strip()
    if not name:
        return None
    try:
        from api import crm as _crm
        # Use the existing search-by-name path
        for c in _crm.list_contacts(business_id, search=name, limit=10):
            full = " ".join(filter(None, [c.get("first_name"), c.get("last_name")])).strip().lower()
            company = (c.get("company_name") or "").lower()
            n = name.lower()
            if n in full or n in company or full.startswith(n.split()[0]):
                return c["id"]
    except Exception as e:
        logger.debug(f"[proposal_tools] name resolution failed: {e}")
    return None


def _generate_proposal(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    business_id = ctx["business_id"]
    brief = (args.get("brief") or "").strip()
    if not brief:
        raise ValueError("brief is required — describe what to propose, for whom, and pricing.")

    contact_id = (args.get("contact_id") or "").strip()
    contact_name = (args.get("contact_name") or "").strip()
    resolved_id = _resolve_contact_id(business_id, contact_id, contact_name)

    overrides = {}
    if not resolved_id and contact_name:
        # No CRM match; still address the proposal to the named recipient
        overrides["name"] = contact_name

    from api import proposals as _proposals
    out = _proposals.generate_proposal(
        business_id=business_id,
        brief=brief,
        contact_id=resolved_id,
        recipient_overrides=overrides or None,
    )

    # The chat UI surfaces tool-result `files` as download buttons. Mirror
    # the schema that other doc-producing tools use (see notification_tools).
    return {
        "ok":           True,
        "id":           out["id"],
        "title":        out["title"],
        "filename":     out["filename"],
        "size_bytes":   out["size_bytes"],
        "recipient":    out["recipient"],
        "files": [{
            "filename":     out["filename"],
            "label":        f"Proposal · {out['title']}",
            "size_bytes":   out["size_bytes"],
            "kind":         "proposal_pdf",
            "id":           out["id"],
        }],
        "message":      (
            f"Generated proposal '{out['title']}' "
            f"({_size_friendly(out['size_bytes'])}). "
            f"Click the download button to view, then attach to your email."
        ),
    }


def _size_friendly(n: int) -> str:
    if n < 1024:        return f"{n} B"
    if n < 1024 * 1024: return f"{n / 1024:.1f} KB"
    return f"{n / 1024 / 1024:.2f} MB"


register_tool(
    name="generate_proposal",
    description=(
        "Generate a professional PDF proposal from a plain-English brief. "
        "Use when the user asks to draft, create, or send a proposal / "
        "quote / quotation. The brief should describe the work, recipient, "
        "and pricing — e.g. 'Proposal for Mehta — 5,000 flyers at Rs 40 "
        "each, delivery by Diwali, 50% advance'. The tool looks up the "
        "named contact in CRM (or accepts contact_id), generates the spec "
        "via LLM, renders a polished PDF, and returns a download link the "
        "chat UI / WhatsApp surfaces automatically."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "brief": {
                "type": "string",
                "description": (
                    "Plain-English description of what to propose: scope, "
                    "quantity, pricing, delivery date, terms. The clearer "
                    "the brief, the better the proposal. Max ~1000 chars."
                ),
            },
            "contact_name": {
                "type": "string",
                "description": "Recipient's name as the user said it. Optional.",
            },
            "contact_id": {
                "type": "string",
                "description": "Existing CRM contact id, if known. Skips the name lookup.",
            },
        },
        "required": ["brief"],
    },
    handler=_generate_proposal,
    summary_fn=lambda a: f"Proposal: {(a.get('brief') or '')[:80]}",
)
