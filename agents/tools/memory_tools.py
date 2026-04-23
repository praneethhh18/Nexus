"""Memory tools — long-term per-business facts the agent can read and write."""
from __future__ import annotations

from agents.tool_registry import register_tool
from agents import business_memory as _mem


def _remember(ctx, args):
    return _mem.add_memory(
        ctx["business_id"], ctx["user_id"],
        content=args["content"],
        kind=args.get("kind", "fact"),
        tags=args.get("tags", ""),
        is_pinned=bool(args.get("pinned", False)),
    )


register_tool(
    name="remember",
    description=(
        "Store a long-term fact or preference about this business that the agent "
        "should remember across sessions. Examples: billing terms, key preferences, "
        "important policies, team member roles. Keep entries concise (< 200 chars)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "content": {"type": "string"},
            "kind": {"type": "string", "description": "fact | preference | policy | contact"},
            "tags": {"type": "string", "description": "Comma-separated tags"},
            "pinned": {"type": "boolean", "default": False},
        },
        "required": ["content"],
    },
    handler=_remember,
    summary_fn=lambda a: f"Remember: {a.get('content', '')[:100]}",
)


def _recall(ctx, args):
    return _mem.list_memory(
        ctx["business_id"],
        search=args.get("search"),
        limit=int(args.get("limit", 30)),
    )


register_tool(
    name="recall",
    description=(
        "Search long-term business memory. Use this BEFORE answering questions "
        "where stored preferences or policies would matter."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "search": {"type": "string"},
            "limit": {"type": "integer", "default": 30},
        },
    },
    handler=_recall,
)


def _consolidate(ctx, args):
    from agents.summarizer import consolidate_business_memory
    return consolidate_business_memory(
        ctx["business_id"],
        apply_changes=bool(args.get("apply", False)),
        preserve_pinned=bool(args.get("preserve_pinned", True)),
    )


register_tool(
    name="consolidate_memory",
    description=(
        "Clean up redundant or stale memory entries for this business. "
        "Pass apply=false first to preview the plan, then apply=true to commit."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "apply": {"type": "boolean", "default": False},
            "preserve_pinned": {"type": "boolean", "default": True},
        },
    },
    handler=_consolidate,
    summary_fn=lambda a: "Consolidate memory" + (" (apply)" if a.get("apply") else " (preview)"),
)


def _forget(ctx, args):
    _mem.delete_memory(ctx["business_id"], args["memory_id"])
    return {"ok": True}


register_tool(
    name="delete_memory",
    description="Remove a specific memory entry by id. Requires approval.",
    input_schema={
        "type": "object",
        "properties": {"memory_id": {"type": "string"}},
        "required": ["memory_id"],
    },
    handler=_forget,
    summary_fn=lambda a: f"FORGET memory {a.get('memory_id')}",
)
