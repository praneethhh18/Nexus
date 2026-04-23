"""
Tool registry — the single source of truth for what the agent can do.

Each tool has:
    name           : stable identifier used by the LLM
    description    : what it does, written for the LLM
    input_schema   : JSON schema (Claude format) — validated before calling
    handler        : (ctx, args) -> result dict. ctx = {business_id, user_id, user_role}
    requires_approval : if True, writes go to the approval queue first
    summary_fn     : (args) -> human-readable one-line summary (for Approvals UI)

Design notes:
- Read tools never require approval.
- Safe writes (create_task, create_contact) execute inline; the action is
  undoable from the UI so this is low-risk.
- Destructive writes and external-facing writes (send_email, send_invoice,
  delete_*) always require approval, even if the user flag says otherwise.
- Every tool handler is passed `ctx` so it can enforce business_id scoping
  and attribute audit log entries.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Callable

from fastapi import HTTPException
from loguru import logger

from agents import approval_queue

# ── Registry storage ─────────────────────────────────────────────────────────
_TOOLS: Dict[str, Dict[str, Any]] = {}

# Tools that ALWAYS require approval, regardless of caller flags.
# These have real-world side effects that can't be easily undone.
_FORCED_APPROVAL = {
    "send_email",
    "send_invoice_email",
    "delete_contact",
    "delete_company",
    "delete_deal",
    "delete_invoice",
    "delete_task",
    "delete_document",
    "delete_memory",
}


def register_tool(
    name: str,
    description: str,
    input_schema: Dict[str, Any],
    handler: Callable,
    requires_approval: bool = False,
    summary_fn: Optional[Callable] = None,
) -> None:
    if name in _TOOLS:
        raise ValueError(f"Tool {name!r} is already registered")
    _TOOLS[name] = {
        "name": name,
        "description": description,
        "input_schema": input_schema,
        "handler": handler,
        "requires_approval": requires_approval or (name in _FORCED_APPROVAL),
        "summary_fn": summary_fn,
    }


def get_tool(name: str) -> Dict[str, Any]:
    tool = _TOOLS.get(name)
    if not tool:
        raise HTTPException(400, f"Unknown tool: {name}")
    return tool


def list_tools(for_llm: bool = False) -> List[Dict[str, Any]]:
    """If for_llm, strip handler/summary_fn before returning."""
    if for_llm:
        return [
            {
                "name": t["name"],
                "description": t["description"],
                "input_schema": t["input_schema"],
            }
            for t in _TOOLS.values()
        ]
    return [
        {
            "name": t["name"],
            "description": t["description"],
            "input_schema": t["input_schema"],
            "requires_approval": t["requires_approval"],
        }
        for t in _TOOLS.values()
    ]


# ── Execution ────────────────────────────────────────────────────────────────
def execute_tool_now(
    tool_name: str,
    arguments: Dict[str, Any],
    business_id: str,
    user_id: str,
    user_role: str = "member",
) -> Any:
    """
    Run a tool directly, bypassing approval (used by the approval queue after
    the user has approved, and by safe inline writes).
    """
    tool = get_tool(tool_name)
    _validate_arguments(tool, arguments)
    ctx = {"business_id": business_id, "user_id": user_id, "user_role": user_role}

    try:
        result = tool["handler"](ctx, arguments)
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"[Tool] {tool_name} failed")
        raise HTTPException(500, f"Tool {tool_name} failed: {e}")

    # Audit log
    try:
        from memory.audit_logger import log_tool_call
        summary = _summarize(tool, arguments)
        log_tool_call(
            tool=f"agent.{tool_name}",
            input_summary=summary[:500],
            output_summary=str(result)[:500],
            approved=True,
            success=True,
            business_id=business_id,
            user_id=user_id,
        )
    except Exception:
        pass
    return result


def invoke_tool(
    tool_name: str,
    arguments: Dict[str, Any],
    business_id: str,
    user_id: str,
    user_role: str = "member",
) -> Dict[str, Any]:
    """
    Agent-facing entry point. Either executes the tool and returns its result,
    OR queues it for approval and returns {"pending_approval": True, ...}.
    """
    tool = get_tool(tool_name)
    _validate_arguments(tool, arguments)

    if tool["requires_approval"]:
        summary = _summarize(tool, arguments)
        action = approval_queue.queue_action(
            business_id=business_id,
            user_id=user_id,
            tool_name=tool_name,
            summary=summary,
            args=arguments,
        )
        return {
            "pending_approval": True,
            "approval_id": action["id"],
            "summary": summary,
            "message": f"I prepared this action for you: {summary}. "
                       f"It's waiting for your approval on the Approvals page.",
        }

    result = execute_tool_now(tool_name, arguments, business_id, user_id, user_role)
    return {"pending_approval": False, "result": result}


def _summarize(tool: Dict[str, Any], arguments: Dict[str, Any]) -> str:
    fn = tool.get("summary_fn")
    if fn:
        try:
            return str(fn(arguments))[:500]
        except Exception:
            pass
    return f"{tool['name']}({', '.join(f'{k}={_short(v)}' for k, v in arguments.items())})"[:500]


def _short(v: Any) -> str:
    s = str(v)
    return s if len(s) <= 40 else s[:37] + "..."


# ── Lightweight validation ───────────────────────────────────────────────────
def _validate_arguments(tool: Dict[str, Any], arguments: Dict[str, Any]) -> None:
    schema = tool.get("input_schema", {})
    required = schema.get("required", [])
    for key in required:
        if key not in arguments or arguments[key] in (None, ""):
            raise HTTPException(400, f"Tool {tool['name']}: missing required argument '{key}'")
    # Spot-check types loosely — Claude usually gives correct types; Ollama sometimes
    # stringifies. We coerce numbers where possible.
    props = schema.get("properties", {})
    for key, spec in props.items():
        if key not in arguments:
            continue
        expected = spec.get("type")
        val = arguments[key]
        if expected == "integer" and isinstance(val, str):
            try:
                arguments[key] = int(val)
            except Exception:
                pass
        elif expected == "number" and isinstance(val, str):
            try:
                arguments[key] = float(val)
            except Exception:
                pass
        elif expected == "boolean" and isinstance(val, str):
            arguments[key] = val.strip().lower() in ("true", "yes", "1")


# ── Register all tools on import ─────────────────────────────────────────────
# (Delayed import to avoid circular refs)
def _register_all():
    from agents.tools import (  # noqa: F401
        crm_tools, task_tools, invoice_tools, document_tools,
        calendar_tools, memory_tools, notification_tools, rag_tools,
        analytics_tools,
    )


_register_all()
logger.info(f"[Tools] Registered {len(_TOOLS)} agent tools")
