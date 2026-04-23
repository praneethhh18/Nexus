"""
NexusAgent LLM Provider — Hybrid system.
Uses Claude API for fast, powerful responses.
Uses local Ollama for embeddings only (keeps data private).

Set ANTHROPIC_API_KEY in .env to enable Claude.
Falls back to local Ollama if no API key is set.
"""
from __future__ import annotations

import os
import time
from typing import Generator
from loguru import logger

from config.settings import OLLAMA_BASE_URL, EMBED_MODEL

# ── Provider Detection ────────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")
USE_CLAUDE = bool(ANTHROPIC_API_KEY)

_client = None
_embed_instance = None


def get_provider() -> str:
    return "claude" if USE_CLAUDE else "ollama"


# ── Claude Client ─────────────────────────────────────────────────────────────
def _get_claude():
    global _client
    if _client is None:
        import anthropic
        _client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        logger.success(f"[LLM] Claude client ready (model: {CLAUDE_MODEL})")
    return _client


def invoke(prompt: str, system: str = "", max_tokens: int = 1024, temperature: float = 0.1) -> str:
    """Send a prompt and get a complete response. Works with both Claude and Ollama."""
    if USE_CLAUDE:
        return _invoke_claude(prompt, system, max_tokens, temperature)
    else:
        return _invoke_ollama(prompt)


def stream(prompt: str, system: str = "", max_tokens: int = 1024) -> Generator[str, None, None]:
    """Stream tokens one by one. Works with both Claude and Ollama."""
    if USE_CLAUDE:
        yield from _stream_claude(prompt, system, max_tokens)
    else:
        yield from _stream_ollama(prompt)


# ── Claude Implementation ─────────────────────────────────────────────────────
def _invoke_claude(prompt: str, system: str, max_tokens: int, temperature: float) -> str:
    client = _get_claude()
    try:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": CLAUDE_MODEL, "max_tokens": max_tokens, "messages": messages, "temperature": temperature}
        if system:
            kwargs["system"] = system
        response = client.messages.create(**kwargs)
        return response.content[0].text
    except Exception as e:
        logger.error(f"[Claude] Invoke failed: {e}")
        raise


def _stream_claude(prompt: str, system: str, max_tokens: int) -> Generator[str, None, None]:
    client = _get_claude()
    try:
        messages = [{"role": "user", "content": prompt}]
        kwargs = {"model": CLAUDE_MODEL, "max_tokens": max_tokens, "messages": messages}
        if system:
            kwargs["system"] = system
        with client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        logger.error(f"[Claude] Stream failed: {e}")
        yield f"\n[Error: {e}]"


# ── Ollama Fallback ───────────────────────────────────────────────────────────
def _invoke_ollama(prompt: str) -> str:
    from config.llm_config import get_llm
    llm = get_llm()
    return llm.invoke(prompt)


def _stream_ollama(prompt: str) -> Generator[str, None, None]:
    from config.llm_config import stream_generate
    yield from stream_generate(prompt)


# ── Embeddings (always local) ─────────────────────────────────────────────────
def get_embedder():
    """Always uses local Ollama for embeddings — data never leaves your machine."""
    global _embed_instance
    if _embed_instance is None:
        from langchain_ollama import OllamaEmbeddings
        _embed_instance = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=EMBED_MODEL)
        logger.success(f"[Embedder] Local '{EMBED_MODEL}' ready (data stays private).")
    return _embed_instance


# ── Health Check ──────────────────────────────────────────────────────────────
def health_check() -> dict:
    result = {"provider": get_provider()}

    if USE_CLAUDE:
        try:
            client = _get_claude()
            # Quick test
            resp = client.messages.create(
                model=CLAUDE_MODEL, max_tokens=5,
                messages=[{"role": "user", "content": "hi"}],
            )
            result["claude"] = {"online": True, "model": CLAUDE_MODEL}
        except Exception as e:
            result["claude"] = {"online": False, "error": str(e)}

    # Always check Ollama (needed for embeddings)
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        models = [m["name"] for m in resp.json().get("models", [])] if resp.status_code == 200 else []
        result["ollama"] = {"online": resp.status_code == 200, "models": len(models), "embed_model": EMBED_MODEL}
    except Exception:
        result["ollama"] = {"online": False}

    return result
