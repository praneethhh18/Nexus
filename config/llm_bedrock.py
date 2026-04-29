"""
Amazon Bedrock adapter — exposes the same `invoke` / `stream` / `invoke_with_tools`
shape as `config/llm_provider.py` so the rest of the app doesn't care which
provider is active.

Uses the Bedrock **Converse API** (not InvokeModel) because it speaks a
unified tool-use format across all model families on Bedrock.

Model routing:
    BEDROCK_MODEL_ID         — primary model used for agent loops and
                               anything reasoning-heavy. Default Nova Pro.
    BEDROCK_FAST_MODEL_ID    — cheaper/faster model used for classification,
                               chitchat, and background jobs. Default Nova Lite.

Translators:
    Our agent code uses Anthropic-style content blocks:
        {"type": "text", "text": "..."}
        {"type": "tool_use", "id": "...", "name": "...", "input": {...}}
        {"type": "tool_result", "tool_use_id": "...", "content": "..."}
    Converse uses:
        {"text": "..."}
        {"toolUse": {"toolUseId": "...", "name": "...", "input": {...}}}
        {"toolResult": {"toolUseId": "...", "content": [{"text": "..."}]}}
    We translate both ways here so callers keep using the Anthropic shape.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from typing import Any, Dict, Generator, List, Optional

from loguru import logger

from config import privacy
from config import cloud_budget


# Nova models emit chain-of-thought inside <thinking>...</thinking> by default.
# Strip them before the text reaches the user — and unwrap any <response>...</response>
# envelope the model may have added.
_THINKING_RE = re.compile(r"<thinking>[\s\S]*?</thinking>", re.IGNORECASE)
_RESPONSE_OPEN_RE = re.compile(r"^\s*<response>\s*", re.IGNORECASE)
_RESPONSE_CLOSE_RE = re.compile(r"\s*</response>\s*$", re.IGNORECASE)


def _clean_model_text(text: str) -> str:
    """Remove <thinking> blocks and unwrap <response> envelopes from Nova output."""
    if not text:
        return ""
    cleaned = _THINKING_RE.sub("", text).strip()
    cleaned = _RESPONSE_OPEN_RE.sub("", cleaned)
    cleaned = _RESPONSE_CLOSE_RE.sub("", cleaned)
    return cleaned.strip()


# ── Client singleton ─────────────────────────────────────────────────────────
_client = None


def _region() -> str:
    return (os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION") or "us-east-1").strip()


def bedrock_available() -> bool:
    """True if AWS creds are present and boto3 is installed."""
    if not (os.getenv("AWS_ACCESS_KEY_ID") and os.getenv("AWS_SECRET_ACCESS_KEY")):
        return False
    try:
        import boto3  # noqa: F401
        return True
    except Exception:
        return False


def _get_client():
    global _client
    if _client is None:
        import boto3
        _client = boto3.client(
            "bedrock-runtime",
            region_name=_region(),
            aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
            aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
            aws_session_token=os.getenv("AWS_SESSION_TOKEN") or None,
        )
        logger.success(f"[Bedrock] Client ready in {_region()} "
                       f"(primary={primary_model_id()}, fast={fast_model_id()})")
    return _client


def primary_model_id() -> str:
    return os.getenv("BEDROCK_MODEL_ID", "us.amazon.nova-pro-v1:0")


def fast_model_id() -> str:
    return os.getenv("BEDROCK_FAST_MODEL_ID", "us.amazon.nova-lite-v1:0")


# ── Translators: messages ───────────────────────────────────────────────────
def _to_bedrock_messages(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert Anthropic-style messages into Bedrock Converse 'messages'."""
    out = []
    for m in messages:
        role = m.get("role", "user")
        if role not in ("user", "assistant"):
            continue
        raw = m.get("content", "")
        content_blocks: List[Dict[str, Any]] = []

        if isinstance(raw, str):
            if raw.strip():
                content_blocks.append({"text": raw})
        elif isinstance(raw, list):
            for b in raw:
                if not isinstance(b, dict):
                    continue
                btype = b.get("type")
                if btype == "text":
                    txt = b.get("text", "")
                    if txt:
                        content_blocks.append({"text": txt})
                elif btype == "tool_use":
                    content_blocks.append({
                        "toolUse": {
                            "toolUseId": b.get("id") or f"tool-{uuid.uuid4().hex[:8]}",
                            "name": b.get("name", ""),
                            "input": b.get("input", {}) or {},
                        }
                    })
                elif btype == "tool_result":
                    # Bedrock tool_result content must be list of content blocks
                    content = b.get("content", "")
                    if isinstance(content, str):
                        tr_content = [{"text": content}]
                    elif isinstance(content, list):
                        tr_content = []
                        for sub in content:
                            if isinstance(sub, dict) and sub.get("type") == "text":
                                tr_content.append({"text": sub.get("text", "")})
                            elif isinstance(sub, str):
                                tr_content.append({"text": sub})
                        if not tr_content:
                            tr_content = [{"text": json.dumps(content, default=str)[:4000]}]
                    else:
                        tr_content = [{"text": json.dumps(content, default=str)[:4000]}]
                    content_blocks.append({
                        "toolResult": {
                            "toolUseId": b.get("tool_use_id") or b.get("id") or "",
                            "content": tr_content,
                        }
                    })
        # Skip empty messages — Bedrock rejects them
        if not content_blocks:
            continue
        out.append({"role": role, "content": content_blocks})
    return out


def _to_bedrock_tools(tools: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Convert Anthropic tool list into Bedrock toolConfig."""
    spec = []
    for t in tools or []:
        spec.append({
            "toolSpec": {
                "name": t.get("name", ""),
                "description": (t.get("description") or "")[:1024],
                "inputSchema": {"json": t.get("input_schema") or {"type": "object", "properties": {}}},
            }
        })
    return {"tools": spec} if spec else {}


def _from_bedrock_response(resp: Dict[str, Any]) -> Dict[str, Any]:
    """Convert a Converse response into the shape our agent loop expects."""
    output = resp.get("output", {})
    message = output.get("message", {}) if isinstance(output, dict) else {}
    blocks = message.get("content", []) if isinstance(message, dict) else []

    text_parts: List[str] = []
    tool_calls: List[Dict[str, Any]] = []
    assistant_content: List[Dict[str, Any]] = []

    for b in blocks:
        if not isinstance(b, dict):
            continue
        if "text" in b:
            cleaned = _clean_model_text(b["text"])
            if cleaned:
                text_parts.append(cleaned)
                assistant_content.append({"type": "text", "text": cleaned})
        elif "toolUse" in b:
            tu = b["toolUse"] or {}
            tool_calls.append({
                "id": tu.get("toolUseId", ""),
                "name": tu.get("name", ""),
                "arguments": tu.get("input", {}) or {},
            })
            assistant_content.append({
                "type": "tool_use",
                "id": tu.get("toolUseId", ""),
                "name": tu.get("name", ""),
                "input": tu.get("input", {}) or {},
            })

    stop_reason_raw = resp.get("stopReason", "end_turn")
    stop_reason = "tool_use" if stop_reason_raw == "tool_use" else (
        "end_turn" if stop_reason_raw in ("end_turn", "stop_sequence", "max_tokens") else stop_reason_raw
    )

    return {
        "stop_reason": stop_reason,
        "text": "\n".join(text_parts).strip(),
        "tool_calls": tool_calls,
        "assistant_content": assistant_content,
    }


# ── Public calls ─────────────────────────────────────────────────────────────
def invoke(prompt: str, system: str = "", max_tokens: int = 1024,
           temperature: float = 0.1, fast: bool = False) -> str:
    """Plain text prompt → text response. No tool use."""
    client = _get_client()
    model = fast_model_id() if fast else primary_model_id()
    red_prompt, red_system, mapping = privacy.prepare_for_cloud(prompt, system)
    audit_rec = privacy.audit_cloud_call("bedrock", model, red_prompt, redactions=len(mapping))
    privacy.note_call("bedrock", cloud=True, redactions=len(mapping),
                      kinds=privacy.kind_counts(mapping), audit_record=audit_rec)
    kwargs = {
        "modelId": model,
        "messages": [{"role": "user", "content": [{"text": red_prompt}]}],
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }
    if red_system:
        kwargs["system"] = [{"text": red_system}]
    try:
        resp = client.converse(**kwargs)
    except Exception as e:
        logger.error(f"[Bedrock] invoke failed: {e}")
        raise
    # Token usage for the budget brake.
    try:
        usage = resp.get("usage") or {}
        cloud_budget.record_usage(
            None, "bedrock", model,
            int(usage.get("inputTokens", 0) or 0),
            int(usage.get("outputTokens", 0) or 0),
        )
    except Exception:
        pass
    msg = resp.get("output", {}).get("message", {})
    parts = [b.get("text", "") for b in msg.get("content", []) if "text" in b]
    return privacy.restore(_clean_model_text("\n".join(parts)), mapping)


def stream(prompt: str, system: str = "", max_tokens: int = 1024,
           fast: bool = False) -> Generator[str, None, None]:
    """Stream text tokens as they're produced."""
    client = _get_client()
    model = fast_model_id() if fast else primary_model_id()
    red_prompt, red_system, mapping = privacy.prepare_for_cloud(prompt, system)
    audit_rec = privacy.audit_cloud_call("bedrock", model, red_prompt,
                                         redactions=len(mapping), metadata={"mode": "stream"})
    privacy.note_call("bedrock", cloud=True, redactions=len(mapping),
                      kinds=privacy.kind_counts(mapping), audit_record=audit_rec)
    kwargs = {
        "modelId": model,
        "messages": [{"role": "user", "content": [{"text": red_prompt}]}],
        "inferenceConfig": {"maxTokens": max_tokens, "temperature": 0.1},
    }
    if red_system:
        kwargs["system"] = [{"text": red_system}]
    try:
        resp = client.converse_stream(**kwargs)
    except Exception as e:
        logger.error(f"[Bedrock] stream failed: {e}")
        yield f"\n[Error: {e}]"
        return

    # Buffer the streamed text so we can strip <thinking> blocks before they
    # hit the user. We emit sanitized chunks as they accumulate, rather than
    # holding the whole response until the end.
    buffer = ""
    in_thinking = False
    for event in resp.get("stream", []):
        if "contentBlockDelta" not in event:
            continue
        delta = event["contentBlockDelta"].get("delta", {})
        chunk = delta.get("text", "")
        if not chunk:
            continue
        buffer += chunk

        # Emit whatever we can safely: everything outside <thinking>…</thinking>
        emit = ""
        while buffer:
            if in_thinking:
                end = buffer.find("</thinking>")
                if end == -1:
                    buffer = ""  # still inside a thinking block, drop everything
                    break
                buffer = buffer[end + len("</thinking>"):]
                in_thinking = False
                continue
            start = buffer.find("<thinking>")
            if start == -1:
                # No open tag in buffer — but keep a tail in case a tag is being streamed in
                if len(buffer) > 20:
                    emit += buffer[:-20]
                    buffer = buffer[-20:]
                break
            emit += buffer[:start]
            buffer = buffer[start + len("<thinking>"):]
            in_thinking = True
        if emit:
            yield privacy.restore(emit, mapping) if mapping else emit
    # Flush any remaining tail (won't contain a half-tag at this point)
    if buffer and not in_thinking:
        tail = _clean_model_text(buffer)
        if tail:
            yield privacy.restore(tail, mapping) if mapping else tail


def invoke_with_tools(
    messages: List[Dict[str, Any]],
    tools: List[Dict[str, Any]],
    system: str = "",
    max_tokens: int = 2048,
    temperature: float = 0.1,
    fast: bool = False,
) -> Dict[str, Any]:
    """One tool-use turn. Returns the agent-loop-shaped dict."""
    client = _get_client()
    model = fast_model_id() if fast else primary_model_id()
    bedrock_messages = _to_bedrock_messages(messages)
    if not bedrock_messages:
        return {"stop_reason": "end_turn", "text": "", "tool_calls": [], "assistant_content": []}

    kwargs = {
        "modelId": model,
        "messages": bedrock_messages,
        "inferenceConfig": {
            "maxTokens": max_tokens,
            "temperature": temperature,
        },
    }
    if system:
        kwargs["system"] = [{"text": system}]
    tool_config = _to_bedrock_tools(tools)
    if tool_config:
        kwargs["toolConfig"] = tool_config

    try:
        resp = client.converse(**kwargs)
    except Exception as e:
        logger.error(f"[Bedrock/tools] call failed: {e}")
        return {
            "stop_reason": "error",
            "text": f"LLM error: {e}",
            "tool_calls": [],
            "assistant_content": [{"type": "text", "text": f"LLM error: {e}"}],
        }

    # Token usage for the budget brake.
    try:
        usage = resp.get("usage") or {}
        cloud_budget.record_usage(
            None, "bedrock", model,
            int(usage.get("inputTokens", 0) or 0),
            int(usage.get("outputTokens", 0) or 0),
        )
    except Exception:
        pass
    return _from_bedrock_response(resp)


# ── Health check ─────────────────────────────────────────────────────────────
def health_check() -> Dict[str, Any]:
    try:
        client = _get_client()
        resp = client.converse(
            modelId=primary_model_id(),
            messages=[{"role": "user", "content": [{"text": "ping"}]}],
            inferenceConfig={"maxTokens": 10, "temperature": 0.0},
        )
        return {
            "online": True,
            "region": _region(),
            "primary_model": primary_model_id(),
            "fast_model": fast_model_id(),
            "latency_hint": resp.get("metrics", {}).get("latencyMs"),
        }
    except Exception as e:
        return {"online": False, "region": _region(), "error": str(e)[:300]}
