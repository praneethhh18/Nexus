"""
NexusAgent LLM Config — Ollama connection, model loading, health checks.
All models run locally via Ollama. No external API calls.
Includes retry logic, connection caching, and graceful degradation.
"""
from __future__ import annotations

import time
import requests
from loguru import logger
from langchain_ollama import OllamaLLM as Ollama
from langchain_ollama import OllamaEmbeddings

from config.settings import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    OLLAMA_FALLBACK_MODEL,
    EMBED_MODEL,
)

# ── Module-level singletons (loaded once, reused) ────────────────────────────
_llm_instance = None
_embed_instance = None
_last_health_check: dict | None = None
_last_health_time: float = 0
_HEALTH_CACHE_SECONDS = 30  # Cache health status to avoid hammering Ollama


def health_check(force: bool = False) -> tuple[bool, str]:
    """
    Ping the Ollama server. Returns (is_healthy, status_message).
    Results are cached for 30 seconds to reduce overhead.
    """
    global _last_health_check, _last_health_time

    if not force and _last_health_check and (time.time() - _last_health_time) < _HEALTH_CACHE_SECONDS:
        return _last_health_check["healthy"], _last_health_check["message"]

    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            msg = f"Ollama online. Models: {', '.join(models) if models else 'none'}"
            logger.info(f"[Ollama] Healthy. {len(models)} models available.")
            _last_health_check = {"healthy": True, "message": msg}
            _last_health_time = time.time()
            return True, msg
        msg = f"Ollama returned HTTP {resp.status_code}"
        _last_health_check = {"healthy": False, "message": msg}
        _last_health_time = time.time()
        return False, msg
    except requests.ConnectionError:
        msg = "Cannot reach Ollama. Run: ollama serve"
        logger.error(f"[Ollama] {msg}")
        _last_health_check = {"healthy": False, "message": msg}
        _last_health_time = time.time()
        return False, msg
    except Exception as e:
        msg = f"Ollama health check failed: {e}"
        logger.error(f"[Ollama] {msg}")
        _last_health_check = {"healthy": False, "message": msg}
        _last_health_time = time.time()
        return False, msg


def _model_available(model_name: str) -> bool:
    """Check if a specific model is available in the local Ollama instance."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            return any(model_name in m for m in models)
    except Exception:
        pass
    return False


def _wait_for_ollama(max_retries: int = 3, base_delay: float = 2.0) -> bool:
    """
    Wait for Ollama to become available with exponential backoff.
    Returns True if connection established, False if all retries exhausted.
    """
    for attempt in range(max_retries):
        healthy, _ = health_check(force=True)
        if healthy:
            return True
        delay = base_delay * (2 ** attempt)
        logger.warning(
            f"[Ollama] Retry {attempt + 1}/{max_retries} — "
            f"waiting {delay:.1f}s before next attempt"
        )
        time.sleep(delay)

    return False


def get_llm(temperature: float = 0.1) -> Ollama:
    """
    Return the LangChain Ollama LLM instance.
    Falls back to OLLAMA_FALLBACK_MODEL if primary is not available.
    Retries connection if Ollama is temporarily unavailable.
    Caches the instance in memory after first load.
    """
    global _llm_instance
    if _llm_instance is not None:
        return _llm_instance

    # Check connection with retry
    healthy, msg = health_check(force=True)
    if not healthy:
        logger.warning("[LLM] Ollama not ready, attempting retry...")
        if not _wait_for_ollama(max_retries=3):
            raise RuntimeError(
                "Could not connect to Ollama after multiple attempts. "
                "Make sure Ollama is running: ollama serve"
            )

    # Select model
    chosen_model = OLLAMA_MODEL
    if not _model_available(OLLAMA_MODEL):
        logger.warning(
            f"[LLM] Primary model '{OLLAMA_MODEL}' not found. "
            f"Trying fallback '{OLLAMA_FALLBACK_MODEL}'."
        )
        chosen_model = OLLAMA_FALLBACK_MODEL
        if not _model_available(OLLAMA_FALLBACK_MODEL):
            logger.error(
                f"[LLM] Fallback model '{OLLAMA_FALLBACK_MODEL}' also not found. "
                f"Attempting to use primary anyway."
            )
            chosen_model = OLLAMA_MODEL

    logger.info(f"[LLM] Loading model: {chosen_model}")
    try:
        _llm_instance = Ollama(
            base_url=OLLAMA_BASE_URL,
            model=chosen_model,
            temperature=temperature,
        )
        logger.success(f"[LLM] Model '{chosen_model}' ready.")
        return _llm_instance
    except Exception as e:
        logger.error(f"[LLM] Failed to load model: {e}")
        raise RuntimeError(
            f"Could not load LLM '{chosen_model}'. "
            "Make sure Ollama is running (ollama serve) and the model is pulled "
            f"(ollama pull {chosen_model})."
        ) from e


def get_embedder() -> OllamaEmbeddings:
    """
    Return the Ollama embedding model instance.
    Uses nomic-embed-text by default (local, no API needed).
    """
    global _embed_instance
    if _embed_instance is not None:
        return _embed_instance

    logger.info(f"[Embedder] Loading embedding model: {EMBED_MODEL}")
    try:
        _embed_instance = OllamaEmbeddings(
            base_url=OLLAMA_BASE_URL,
            model=EMBED_MODEL,
        )
        logger.success(f"[Embedder] Model '{EMBED_MODEL}' ready.")
        return _embed_instance
    except Exception as e:
        logger.error(f"[Embedder] Failed to load embedder: {e}")
        raise RuntimeError(
            f"Could not load embedding model '{EMBED_MODEL}'. "
            "Make sure Ollama is running and the model is pulled: "
            f"ollama pull {EMBED_MODEL}"
        ) from e


def reset_instances():
    """Force reload of LLM/embedder instances (useful for model switching)."""
    global _llm_instance, _embed_instance, _last_health_check, _last_health_time
    _llm_instance = None
    _embed_instance = None
    _last_health_check = None
    _last_health_time = 0
    logger.info("[LLM] Model instances reset.")
