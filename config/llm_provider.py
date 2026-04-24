"""
NexusAgent LLM Provider — unified interface across Claude / Bedrock / Ollama.

Auto-selection order (first match wins):
    1. Anthropic direct — if ANTHROPIC_API_KEY is set
    2. Amazon Bedrock   — if AWS_ACCESS_KEY_ID + AWS_SECRET_ACCESS_KEY are set
    3. Local Ollama     — fallback, always available

Callers don't care which provider is live — they call `invoke()`, `stream()`,
or (via `config.llm_tools.invoke_with_tools`) the tool-calling entry point.

The `fast=True` flag asks for the cheaper/faster model tier (e.g. Nova Lite).
Providers that don't have a fast tier just ignore the flag.
"""
from __future__ import annotations

import os
from typing import Generator
from loguru import logger

from config.settings import OLLAMA_BASE_URL, EMBED_MODEL
from config import privacy

# ── Provider detection ──────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip()
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

USE_CLAUDE = bool(ANTHROPIC_API_KEY)

# Bedrock is only considered if Anthropic direct isn't set
try:
    from config.llm_bedrock import bedrock_available as _bedrock_available
    USE_BEDROCK = (not USE_CLAUDE) and _bedrock_available()
except Exception:
    USE_BEDROCK = False


def get_provider() -> str:
    if USE_CLAUDE:
        return "claude"
    if USE_BEDROCK:
        return "bedrock"
    return "ollama"


_claude_client = None
_embed_instance = None


# ── Claude (direct Anthropic) ────────────────────────────────────────────────
def _get_claude():
    global _claude_client
    if _claude_client is None:
        import anthropic
        _claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.success(f"[LLM] Claude client ready (model: {CLAUDE_MODEL})")
    return _claude_client


def _invoke_claude(prompt: str, system: str, max_tokens: int, temperature: float) -> str:
    client = _get_claude()
    red_prompt, red_system, mapping = privacy.prepare_for_cloud(prompt, system)
    privacy.audit_cloud_call("claude", CLAUDE_MODEL, red_prompt, redactions=len(mapping))
    privacy.note_call("claude", cloud=True, redactions=len(mapping),
                      kinds=privacy.kind_counts(mapping))
    try:
        messages = [{"role": "user", "content": red_prompt}]
        kwargs = {"model": CLAUDE_MODEL, "max_tokens": max_tokens,
                  "messages": messages, "temperature": temperature}
        if red_system:
            kwargs["system"] = red_system
        response = client.messages.create(**kwargs)
        return privacy.restore(response.content[0].text, mapping)
    except Exception as e:
        logger.error(f"[Claude] Invoke failed: {e}")
        raise


def _stream_claude(prompt: str, system: str, max_tokens: int) -> Generator[str, None, None]:
    client = _get_claude()
    red_prompt, red_system, mapping = privacy.prepare_for_cloud(prompt, system)
    privacy.audit_cloud_call("claude", CLAUDE_MODEL, red_prompt,
                             redactions=len(mapping), metadata={"mode": "stream"})
    privacy.note_call("claude", cloud=True, redactions=len(mapping),
                      kinds=privacy.kind_counts(mapping))
    try:
        messages = [{"role": "user", "content": red_prompt}]
        kwargs = {"model": CLAUDE_MODEL, "max_tokens": max_tokens, "messages": messages}
        if red_system:
            kwargs["system"] = red_system
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield privacy.restore(text, mapping) if mapping else text
    except Exception as e:
        logger.error(f"[Claude] Stream failed: {e}")
        yield f"\n[Error: {e}]"


# ── Ollama ───────────────────────────────────────────────────────────────────
def _invoke_ollama(prompt: str) -> str:
    from config.llm_config import get_llm
    llm = get_llm()
    privacy.note_call("ollama", cloud=False, redactions=0)
    return llm.invoke(prompt)


def _stream_ollama(prompt: str) -> Generator[str, None, None]:
    from config.llm_config import stream_generate
    privacy.note_call("ollama", cloud=False, redactions=0)
    yield from stream_generate(prompt)


# ── Unified entry points ─────────────────────────────────────────────────────
def invoke(prompt: str, system: str = "", max_tokens: int = 1024,
           temperature: float = 0.1, fast: bool = False,
           sensitive: bool = False) -> str:
    """
    Plain prompt → text. `fast=True` routes to the cheaper model tier when supported.

    `sensitive=True` forces the request to stay on the local Ollama model even if
    a cloud provider is configured. Use this for any prompt that includes raw DB
    rows, customer records, credentials, or internal business data.
    """
    use_cloud = privacy.should_use_cloud(sensitive, cloud_available=(USE_CLAUDE or USE_BEDROCK))
    if use_cloud and USE_CLAUDE:
        return _invoke_claude(prompt, system, max_tokens, temperature)
    if use_cloud and USE_BEDROCK:
        from config import llm_bedrock
        return llm_bedrock.invoke(prompt, system=system, max_tokens=max_tokens,
                                  temperature=temperature, fast=fast)
    return _invoke_ollama(prompt)


def stream(prompt: str, system: str = "", max_tokens: int = 1024,
           fast: bool = False, sensitive: bool = False) -> Generator[str, None, None]:
    """Stream text tokens one by one. See `invoke` for the sensitive flag."""
    use_cloud = privacy.should_use_cloud(sensitive, cloud_available=(USE_CLAUDE or USE_BEDROCK))
    if use_cloud and USE_CLAUDE:
        yield from _stream_claude(prompt, system, max_tokens)
        return
    if use_cloud and USE_BEDROCK:
        from config import llm_bedrock
        yield from llm_bedrock.stream(prompt, system=system, max_tokens=max_tokens, fast=fast)
        return
    yield from _stream_ollama(prompt)


# ── Embeddings (always local — keeps RAG private) ───────────────────────────
def get_embedder():
    """
    Always uses local Ollama for embeddings. The knowledge base / RAG stays
    100% private regardless of which chat LLM is active.
    """
    global _embed_instance
    if _embed_instance is None:
        from langchain_ollama import OllamaEmbeddings
        _embed_instance = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=EMBED_MODEL)
        logger.success(f"[Embedder] Local '{EMBED_MODEL}' ready (data stays private).")
    return _embed_instance


# ── Health check ─────────────────────────────────────────────────────────────
def health_check() -> dict:
    result = {"provider": get_provider()}

    if USE_CLAUDE:
        try:
            client = _get_claude()
            resp = client.messages.create(
                model=CLAUDE_MODEL, max_tokens=5,
                messages=[{"role": "user", "content": "hi"}],
            )
            result["claude"] = {"online": True, "model": CLAUDE_MODEL}
        except Exception as e:
            result["claude"] = {"online": False, "error": str(e)}

    if USE_BEDROCK:
        try:
            from config import llm_bedrock
            result["bedrock"] = llm_bedrock.health_check()
        except Exception as e:
            result["bedrock"] = {"online": False, "error": str(e)}

    # Always check Ollama (needed for embeddings regardless of provider)
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])] if resp.status_code == 200 else []
        result["ollama"] = {
            "online": resp.status_code == 200,
            "models": len(models),
            "embed_model": EMBED_MODEL,
        }
    except Exception:
        result["ollama"] = {"online": False}

    return result
