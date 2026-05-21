"""NVIDIA NIM provider — OpenAI-compatible API for evaluating Nemotron /
Kimi / GLM / DeepSeek / Llama-4 models against the same agent loop the
production Bedrock path uses.

Activated ONLY when NEXUS_LLM_PROVIDER=nim. Production stays on Bedrock
unchanged — this is a parallel path the test harness flips on to
benchmark alternatives before paying for them.

Translates between two tool-calling conventions:
  - Internal / Anthropic format (what agent_loop and llm_tools speak):
      tool def       : {name, description, input_schema}
      assistant turn : content = [{type:"tool_use", id, name, input}, {type:"text"}]
      tool result    : content = [{type:"tool_result", tool_use_id, content}]
  - OpenAI format (what NIM speaks):
      tool def       : {type:"function", function:{name, description, parameters}}
      assistant turn : tool_calls = [{id, type:"function", function:{name, arguments(str)}}]
      tool result    : {role:"tool", tool_call_id, content}
"""
from __future__ import annotations

import json
import os
import uuid
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from config import privacy

_client = None


def nim_available() -> bool:
    """True if NIM credentials are present and openai SDK is importable."""
    if not os.getenv("NEXUS_NIM_API_KEY"):
        return False
    try:
        import openai  # noqa: F401
        return True
    except Exception:
        return False


def _get_client():
    global _client
    if _client is None:
        from openai import OpenAI
        _client = OpenAI(
            base_url=os.getenv("NEXUS_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1"),
            api_key=os.getenv("NEXUS_NIM_API_KEY"),
        )
        logger.success(f"[NIM] Client ready (model={_model_id()})")
    return _client


def _model_id() -> str:
    return os.getenv("NEXUS_NIM_MODEL", "nvidia/nemotron-3-super-120b-a12b")


# ── Plain invoke (used by config.llm_provider's _invoke_nim shim) ──────────
def invoke(prompt: str, system: str = "", max_tokens: int = 1024,
           temperature: float = 0.1) -> str:
    """Single-turn, no tools. Used for simple text generation calls."""
    client = _get_client()
    red_prompt, red_system, mapping = privacy.prepare_for_cloud(prompt, system)
    privacy.note_call("nim", cloud=True, redactions=len(mapping))
    messages = []
    if red_system:
        messages.append({"role": "system", "content": red_system})
    messages.append({"role": "user", "content": red_prompt})
    resp = client.chat.completions.create(
        model=_model_id(),
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
    )
    raw = (resp.choices[0].message.content or "").strip()
    return privacy.restore(raw, mapping)


# ── Format conversion ─────────────────────────────────────────────────────
def _anthropic_to_openai_tools(tools: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert our internal tool schema to OpenAI function-calling format."""
    out = []
    for t in tools:
        out.append({
            "type": "function",
            "function": {
                "name": t["name"],
                "description": (t.get("description") or "")[:1024],
                "parameters": t.get("input_schema") or {"type": "object", "properties": {}},
            },
        })
    return out


def _anthropic_to_openai_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert agent_loop's Anthropic-shaped messages to OpenAI shape.

    User text                                    -> {role:user, content:str}
    Assistant text                               -> {role:assistant, content:str}
    Assistant with tool_use blocks               -> {role:assistant, content?, tool_calls:[...]}
    User with tool_result blocks                 -> N x {role:tool, tool_call_id, content}
    """
    out: List[Dict[str, Any]] = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")

        if isinstance(content, str):
            out.append({"role": role, "content": content})
            continue

        if not isinstance(content, list):
            out.append({"role": role, "content": str(content)})
            continue

        if role == "assistant":
            text_parts: List[str] = []
            tool_calls: List[Dict[str, Any]] = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    t = block.get("text", "")
                    if t:
                        text_parts.append(t)
                elif btype == "tool_use":
                    tool_calls.append({
                        "id": block.get("id") or f"call_{uuid.uuid4().hex[:8]}",
                        "type": "function",
                        "function": {
                            "name": block.get("name", ""),
                            "arguments": json.dumps(block.get("input", {})),
                        },
                    })
            msg: Dict[str, Any] = {"role": "assistant"}
            if text_parts:
                msg["content"] = "\n".join(text_parts)
            else:
                # OpenAI requires content to be set even when empty alongside tool_calls
                msg["content"] = None
            if tool_calls:
                msg["tool_calls"] = tool_calls
            out.append(msg)
            continue

        if role == "user":
            # Walk blocks; tool_result blocks become separate role:tool messages.
            text_parts: List[str] = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    t = block.get("text", "")
                    if t:
                        text_parts.append(t)
                elif btype == "tool_result":
                    raw = block.get("content", "")
                    if not isinstance(raw, str):
                        try:
                            raw = json.dumps(raw)
                        except Exception:
                            raw = str(raw)
                    out.append({
                        "role": "tool",
                        "tool_call_id": block.get("tool_use_id") or "",
                        "content": raw,
                    })
            if text_parts:
                out.append({"role": "user", "content": "\n".join(text_parts)})
            continue

        # Fallback for any other role
        out.append({"role": role, "content": json.dumps(content)})

    return out


# ── invoke_with_tools (the real workhorse) ─────────────────────────────────
def invoke_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.1,
) -> Dict[str, Any]:
    """One LLM turn with tool use. Mirrors the shape llm_tools.invoke_with_tools
    returns so agent_loop doesn't care which provider answered."""
    client = _get_client()

    # Redact PII before send. Mirrors what _invoke_claude_tools does.
    from config.llm_tools import _redact_messages
    red_messages, mapping = _redact_messages(messages)
    red_system, sys_map = privacy.redact(system or "")
    mapping.update(sys_map)

    oai_messages = _anthropic_to_openai_messages(red_messages)
    if red_system:
        oai_messages.insert(0, {"role": "system", "content": red_system})

    oai_tools = _anthropic_to_openai_tools(tools)

    privacy.note_call("nim", cloud=True, redactions=len(mapping),
                      kinds=privacy.kind_counts(mapping))
    try:
        resp = client.chat.completions.create(
            model=_model_id(),
            messages=oai_messages,
            tools=oai_tools if oai_tools else None,
            tool_choice="auto" if oai_tools else None,
            temperature=temperature,
            max_tokens=max_tokens,
        )
    except Exception as e:
        logger.error(f"[NIM/Tools] Call failed: {e}")
        return {
            "stop_reason": "error",
            "text": f"NIM error: {e}",
            "tool_calls": [],
            "assistant_content": [{"type": "text", "text": f"NIM error: {e}"}],
        }

    choice = resp.choices[0]
    msg = choice.message
    text = (msg.content or "")
    text = privacy.restore(text, mapping) if text else ""

    tool_calls_out: List[Dict[str, Any]] = []
    assistant_blocks: List[Dict[str, Any]] = []
    if text:
        assistant_blocks.append({"type": "text", "text": text})

    raw_tcs = getattr(msg, "tool_calls", None) or []
    for tc in raw_tcs:
        try:
            fn = tc.function
            tid = tc.id or f"call_{uuid.uuid4().hex[:8]}"
            try:
                args = json.loads(fn.arguments or "{}")
            except Exception:
                args = {}
            args = {k: (privacy.restore(v, mapping) if isinstance(v, str) else v)
                    for k, v in args.items()}
            tool_calls_out.append({"id": tid, "name": fn.name, "arguments": args})
            assistant_blocks.append({
                "type": "tool_use", "id": tid, "name": fn.name, "input": args,
            })
        except Exception as e:
            logger.warning(f"[NIM/Tools] couldn't parse a tool call: {e}")

    finish = choice.finish_reason or "stop"
    stop_reason = "tool_use" if tool_calls_out else (
        "end_turn" if finish in ("stop", "length") else finish
    )

    return {
        "stop_reason": stop_reason,
        "text": text,
        "tool_calls": tool_calls_out,
        "assistant_content": assistant_blocks or [{"type": "text", "text": ""}],
    }
