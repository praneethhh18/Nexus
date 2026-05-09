"""Per-contact memory tools — let the agent remember and recall facts about
specific contacts so every conversation feels like a continuation, not a cold start.
"""
from __future__ import annotations

from typing import Any, Dict

from agents.tool_registry import register_tool


def _remember_about_contact(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import contact_memory as _cm
    contact_id = (args.get("contact_id") or "").strip()
    fact       = (args.get("fact") or "").strip()
    kind       = (args.get("kind") or "note").strip().lower()
    if not contact_id or not fact:
        raise ValueError("contact_id and fact are both required")
    out = _cm.remember(
        business_id=ctx["business_id"], contact_id=contact_id, fact=fact,
        kind=kind, source="agent", confidence=int(args.get("confidence", 80)),
        created_by=ctx.get("user_id"),
    )
    return {"ok": True, "id": out["id"], "kind": out["kind"], "fact": out["fact"]}


register_tool(
    name="remember_about_contact",
    description=(
        "Save one durable fact about a specific contact. Use when the user "
        "tells you something worth remembering across future interactions — "
        "preferences ('Mehta prefers Net-30'), objections ('cost concerns "
        "on tier 2'), context ('CFO Anjali has to approve > 3L'), promises "
        "('will share menu by Friday'), or personal touches ('kids' admissions "
        "in May'). Kind is one of preference/objection/context/promise/personal/note."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "contact_id": {"type": "string"},
            "fact":       {"type": "string", "description": "Short, durable, action-relevant. Max 1000 chars."},
            "kind": {
                "type": "string",
                "enum": ["preference", "objection", "context", "promise", "personal", "note"],
                "default": "note",
            },
            "confidence": {"type": "integer", "default": 80, "description": "0-100 self-rated confidence."},
        },
        "required": ["contact_id", "fact"],
    },
    handler=_remember_about_contact,
    summary_fn=lambda a: f"Remember about {a.get('contact_id','?')}: {(a.get('fact') or '')[:80]}",
)


def _recall_contact(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import contact_memory as _cm
    contact_id = (args.get("contact_id") or "").strip()
    if not contact_id:
        raise ValueError("contact_id is required")
    facts = _cm.recall(ctx["business_id"], contact_id, limit=int(args.get("limit", 25)))
    brief = _cm.build_brief(ctx["business_id"], contact_id, max_facts=int(args.get("limit", 25)))
    return {
        "ok":       True,
        "count":    len(facts),
        "facts":    [{"id": f["id"], "kind": f["kind"], "fact": f["fact"],
                      "source": f.get("source"), "created_at": f["created_at"]}
                     for f in facts],
        "brief":    brief,  # ready-to-paste prompt block
    }


register_tool(
    name="recall_contact",
    description=(
        "Fetch everything we know about a specific contact from per-contact "
        "memory. Returns both the structured fact list and a pre-formatted "
        "'brief' block you can drop straight into a prompt for Vox/Iris/"
        "Outreach to use. Always call this BEFORE drafting a message or call "
        "script for a known contact."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "contact_id": {"type": "string"},
            "limit":      {"type": "integer", "default": 25, "description": "Max facts to return (default 25)."},
        },
        "required": ["contact_id"],
    },
    handler=_recall_contact,
    summary_fn=lambda a: f"Recall facts for contact {a.get('contact_id','?')}",
)


def _forget_contact_fact(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    from api import contact_memory as _cm
    mid = (args.get("memory_id") or "").strip()
    if not mid:
        raise ValueError("memory_id is required")
    archived = _cm.forget(ctx["business_id"], mid)
    return {"ok": archived, "memory_id": mid,
            "message": "Forgotten." if archived else "No matching active memory found."}


register_tool(
    name="forget_contact_fact",
    description="Soft-delete one specific contact-memory fact by id. Use when the user explicitly says a fact is wrong or stale.",
    input_schema={
        "type": "object",
        "properties": {"memory_id": {"type": "string"}},
        "required": ["memory_id"],
    },
    handler=_forget_contact_fact,
    summary_fn=lambda a: f"Forget memory {a.get('memory_id','?')}",
)
