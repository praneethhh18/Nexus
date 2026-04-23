"""
Tool-calling layer for the LLM provider.

Provides a unified `invoke_with_tools(messages, tools)` across Claude (native
tool use) and Ollama (ReAct-style structured JSON prompt fallback).

Returns a dict:
    {
      "stop_reason": "tool_use" | "end_turn",
      "text": "<free text portion>",
      "tool_calls": [{id, name, arguments}],
    }

The caller runs the tools and loops by appending assistant and tool-result
messages until stop_reason == "end_turn" or a safety cap is hit.
"""
from __future__ import annotations

import json
import re
import uuid
from typing import List, Dict, Any, Optional

from loguru import logger

from config.llm_provider import USE_CLAUDE, USE_BEDROCK, _get_claude, CLAUDE_MODEL, invoke as plain_invoke
from config import privacy


# ── Public API ───────────────────────────────────────────────────────────────
def invoke_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.1,
    fast: bool = False,
    sensitive: bool = False,
) -> Dict[str, Any]:
    """
    Run a single LLM turn with tool use enabled.

    messages: list of {role, content} where content can be:
        - str (user/assistant text)
        - list of content blocks (assistant tool_use, user tool_result)
          matching Claude's message format.

    tools: list of {name, description, input_schema} — same format Claude uses.

    sensitive: when True, forces the local Ollama tool-use path even if a cloud
    provider is configured. Use for agents that handle raw DB rows, customer
    records, or internal business data.
    """
    use_cloud = privacy.should_use_cloud(sensitive, cloud_available=(USE_CLAUDE or USE_BEDROCK))
    if use_cloud and USE_CLAUDE:
        return _invoke_claude_tools(messages, tools, system, max_tokens, temperature)
    if use_cloud and USE_BEDROCK:
        from config import llm_bedrock
        return llm_bedrock.invoke_with_tools(
            messages=messages, tools=tools, system=system,
            max_tokens=max_tokens, temperature=temperature, fast=fast,
        )
    return _invoke_ollama_tools(messages, tools, system, max_tokens)


def _redact_messages(messages: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], Dict[str, str]]:
    """Walk Claude-format messages and redact every string/text/tool_result payload."""
    mapping: Dict[str, str] = {}

    def _red(txt: str) -> str:
        red, m = privacy.redact(txt or "")
        mapping.update(m)
        return red

    redacted: List[Dict[str, Any]] = []
    for msg in messages:
        content = msg.get("content", "")
        if isinstance(content, str):
            redacted.append({**msg, "content": _red(content)})
        elif isinstance(content, list):
            new_blocks = []
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    new_blocks.append({**block, "text": _red(block.get("text", ""))})
                elif btype == "tool_result":
                    raw = block.get("content", "")
                    if isinstance(raw, str):
                        new_blocks.append({**block, "content": _red(raw)})
                    else:
                        # tool results can be a list of content blocks too
                        new_blocks.append({**block, "content": _red(json.dumps(raw))})
                else:
                    new_blocks.append(block)
            redacted.append({**msg, "content": new_blocks})
        else:
            redacted.append(msg)
    return redacted, mapping


# ── Claude native tool use ───────────────────────────────────────────────────
def _invoke_claude_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system: str,
    max_tokens: int,
    temperature: float,
) -> Dict[str, Any]:
    client = _get_claude()
    red_messages, mapping = _redact_messages(messages)
    red_system, sys_map = privacy.redact(system or "")
    mapping.update(sys_map)
    privacy.audit_cloud_call(
        "claude", CLAUDE_MODEL,
        prompt=json.dumps(red_messages)[:4000],
        redactions=len(mapping),
        metadata={"mode": "tools", "tool_count": len(tools)},
    )
    try:
        kwargs = {
            "model": CLAUDE_MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": red_messages,
            "tools": tools,
        }
        if red_system:
            kwargs["system"] = red_system
        response = client.messages.create(**kwargs)

        text_parts = []
        tool_calls = []
        for block in response.content:
            btype = getattr(block, "type", None)
            if btype == "text":
                text_parts.append(privacy.restore(block.text, mapping))
            elif btype == "tool_use":
                args = dict(block.input) if block.input else {}
                # Restore any tokens the model echoed back inside tool arguments
                args = {k: (privacy.restore(v, mapping) if isinstance(v, str) else v)
                        for k, v in args.items()}
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "arguments": args,
                })

        return {
            "stop_reason": response.stop_reason,
            "text": "\n".join(text_parts).strip(),
            "tool_calls": tool_calls,
            # Keep raw assistant content blocks for conversation replay
            "assistant_content": [_serialize_block(b, mapping) for b in response.content],
        }
    except Exception as e:
        logger.error(f"[Tools/Claude] Call failed: {e}")
        return {
            "stop_reason": "error",
            "text": f"LLM error: {e}",
            "tool_calls": [],
            "assistant_content": [{"type": "text", "text": f"LLM error: {e}"}],
        }


def _serialize_block(block, mapping: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    btype = getattr(block, "type", None)
    mapping = mapping or {}
    if btype == "text":
        return {"type": "text", "text": privacy.restore(block.text, mapping)}
    if btype == "tool_use":
        raw = dict(block.input) if block.input else {}
        restored = {k: (privacy.restore(v, mapping) if isinstance(v, str) else v)
                    for k, v in raw.items()}
        return {
            "type": "tool_use",
            "id": block.id,
            "name": block.name,
            "input": restored,
        }
    return {"type": btype or "unknown"}


# ── Ollama ReAct-style fallback ──────────────────────────────────────────────
# Local models don't reliably produce Claude's tool_use format. We instead
# prompt them to emit one JSON object per turn with either a final answer
# or a tool call, and parse it defensively.
_TOOL_PROMPT_TEMPLATE = """You are a helpful assistant with access to tools. \
You MUST respond with a single JSON object and nothing else, in one of these two formats:

To call a tool:
{{"action": "tool", "tool": "<tool_name>", "arguments": {{...}}, "reasoning": "<brief why>"}}

To give a final answer (no more tools needed):
{{"action": "final", "answer": "<your answer to the user>"}}

Available tools:
{tool_descriptions}

Rules:
- Respond with JSON only. Do not wrap in markdown.
- Use a tool if the user is asking you to do, create, update, find, or look up something that needs a tool.
- If the user is just chatting or asking general questions, give a final answer.
- Arguments must match the tool's input_schema exactly.
"""


def _invoke_ollama_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system: str,
    max_tokens: int,
) -> Dict[str, Any]:
    tool_desc_lines = []
    for t in tools:
        schema = t.get("input_schema", {})
        props = schema.get("properties", {})
        required = schema.get("required", [])
        arg_desc = ", ".join(
            f"{k}{'*' if k in required else ''}: {v.get('type', 'any')}"
            for k, v in props.items()
        )
        tool_desc_lines.append(f"- {t['name']}({arg_desc}) — {t.get('description', '')[:120]}")
    tool_block = "\n".join(tool_desc_lines) if tool_desc_lines else "(no tools available)"

    react_system = (system + "\n\n" if system else "") + _TOOL_PROMPT_TEMPLATE.format(
        tool_descriptions=tool_block,
    )

    # Flatten messages into a single prompt. Each tool_result block becomes an
    # "Observation:" line so the model can continue reasoning.
    prompt_parts = []
    for m in messages:
        role = m.get("role", "user")
        content = m.get("content", "")
        if isinstance(content, str):
            prompt_parts.append(f"{role.upper()}: {content}")
        elif isinstance(content, list):
            for block in content:
                btype = block.get("type")
                if btype == "text":
                    prompt_parts.append(f"{role.upper()}: {block.get('text', '')}")
                elif btype == "tool_use":
                    prompt_parts.append(
                        f"ASSISTANT (previous tool call): "
                        f"{json.dumps({'tool': block.get('name'), 'arguments': block.get('input', {})})}"
                    )
                elif btype == "tool_result":
                    prompt_parts.append(
                        f"OBSERVATION: {json.dumps(block.get('content', ''))[:1500]}"
                    )
    prompt_parts.append("ASSISTANT (respond with JSON only):")
    prompt = "\n".join(prompt_parts)

    raw = plain_invoke(prompt, system=react_system, max_tokens=max_tokens, temperature=0.1)
    parsed = _safe_parse_json(raw)

    if not parsed:
        # Model didn't produce JSON — treat as final answer
        return {
            "stop_reason": "end_turn",
            "text": raw.strip(),
            "tool_calls": [],
            "assistant_content": [{"type": "text", "text": raw.strip()}],
        }

    action = parsed.get("action")
    if action == "tool":
        tool_name = parsed.get("tool", "")
        arguments = parsed.get("arguments", {}) or {}
        if not isinstance(arguments, dict):
            arguments = {}
        tid = f"tool-{uuid.uuid4().hex[:8]}"
        return {
            "stop_reason": "tool_use",
            "text": parsed.get("reasoning", "").strip(),
            "tool_calls": [{"id": tid, "name": tool_name, "arguments": arguments}],
            "assistant_content": [
                {"type": "tool_use", "id": tid, "name": tool_name, "input": arguments},
            ],
        }

    # action == "final" (or anything else)
    answer = parsed.get("answer") or parsed.get("text") or raw.strip()
    return {
        "stop_reason": "end_turn",
        "text": str(answer).strip(),
        "tool_calls": [],
        "assistant_content": [{"type": "text", "text": str(answer).strip()}],
    }


_JSON_OBJ_RE = re.compile(r"\{[\s\S]*\}")


def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Find and parse a JSON object in the model output. Defensive."""
    if not text:
        return None
    # Try direct parse
    stripped = text.strip()
    if stripped.startswith("```"):
        # Strip fenced code block
        stripped = re.sub(r"^```(?:json)?|```$", "", stripped.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(stripped)
    except Exception:
        pass
    # Fall back to the first {...} block
    m = _JSON_OBJ_RE.search(stripped)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            return None
    return None
