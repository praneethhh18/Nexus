"""
NexusAgent LLM Config — Dual-model system for speed + power.
Fast model (1.5-3B) for chat/classification. Power model (8B) for data/SQL/reports.
Includes streaming support via Ollama API.
"""
from __future__ import annotations

import time
import json
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

# ── Model instances ───────────────────────────────────────────────────────────
_power_llm = None   # 8B model for SQL, RAG, reports
_fast_llm = None    # Small model for chat, classification
_embed_instance = None
_last_health_check = None
_last_health_time = 0
_HEALTH_CACHE_SECONDS = 120

# Auto-detect best fast model from what's available
_FAST_MODEL_PREFERENCES = [
    "qwen2.5:1.5b-instruct",
    "qwen2.5:3b-instruct-q4_K_M",
    "llama3.2:3b",
    "llama3.2:1b",
    "qwen2.5:0.5b-instruct",
    "qwen3:0.6b",
    "gemma:2b",
    "tinyllama:latest",
]


def health_check(force: bool = False) -> tuple[bool, str]:
    global _last_health_check, _last_health_time
    if not force and _last_health_check and (time.time() - _last_health_time) < _HEALTH_CACHE_SECONDS:
        return _last_health_check["healthy"], _last_health_check["message"]
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            msg = f"Ollama online. {len(models)} models."
            _last_health_check = {"healthy": True, "message": msg}
            _last_health_time = time.time()
            return True, msg
        msg = f"Ollama HTTP {resp.status_code}"
        _last_health_check = {"healthy": False, "message": msg}
        _last_health_time = time.time()
        return False, msg
    except requests.ConnectionError:
        msg = "Cannot reach Ollama. Run: ollama serve"
        _last_health_check = {"healthy": False, "message": msg}
        _last_health_time = time.time()
        return False, msg
    except Exception as e:
        msg = f"Health check failed: {e}"
        _last_health_check = {"healthy": False, "message": msg}
        _last_health_time = time.time()
        return False, msg


def _get_available_models() -> list[str]:
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            return [m["name"] for m in resp.json().get("models", [])]
    except Exception:
        pass
    return []


def _model_available(model_name: str) -> bool:
    models = _get_available_models()
    return any(model_name in m for m in models)


def _pick_fast_model() -> str:
    """Auto-select the best small model available."""
    available = _get_available_models()
    for pref in _FAST_MODEL_PREFERENCES:
        if any(pref in m for m in available):
            logger.info(f"[LLM] Fast model selected: {pref}")
            return pref
    # Fallback to the main model
    return OLLAMA_FALLBACK_MODEL


def get_llm(temperature: float = 0.1) -> Ollama:
    """Return the POWER model (8B) for SQL, RAG, reports, synthesis."""
    global _power_llm
    if _power_llm is not None:
        return _power_llm

    healthy, _ = health_check(force=True)
    if not healthy:
        # One retry
        time.sleep(2)
        healthy, _ = health_check(force=True)
        if not healthy:
            raise RuntimeError("Cannot connect to Ollama. Run: ollama serve")

    chosen = OLLAMA_MODEL
    if not _model_available(OLLAMA_MODEL):
        chosen = OLLAMA_FALLBACK_MODEL

    logger.info(f"[LLM] Loading power model: {chosen}")
    _power_llm = Ollama(base_url=OLLAMA_BASE_URL, model=chosen, temperature=temperature)
    logger.success(f"[LLM] Power model '{chosen}' ready.")
    return _power_llm


def get_fast_llm(temperature: float = 0.1) -> Ollama:
    """Return the FAST model (1.5-3B) for chat, classification, intent detection."""
    global _fast_llm
    if _fast_llm is not None:
        return _fast_llm

    fast_model = _pick_fast_model()
    logger.info(f"[LLM] Loading fast model: {fast_model}")
    _fast_llm = Ollama(base_url=OLLAMA_BASE_URL, model=fast_model, temperature=temperature)
    logger.success(f"[LLM] Fast model '{fast_model}' ready.")
    return _fast_llm


def get_embedder() -> OllamaEmbeddings:
    global _embed_instance
    if _embed_instance is not None:
        return _embed_instance
    _embed_instance = OllamaEmbeddings(base_url=OLLAMA_BASE_URL, model=EMBED_MODEL)
    logger.success(f"[Embedder] '{EMBED_MODEL}' ready.")
    return _embed_instance


def stream_generate(prompt: str, model: str = None) -> iter:
    """Stream tokens from Ollama. Yields text chunks as they arrive.
    This is the key to low-latency chat — first token in <1 second."""
    if model is None:
        model = _pick_fast_model()

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={"model": model, "prompt": prompt, "stream": True},
            stream=True, timeout=120,
        )
        for line in resp.iter_lines():
            if line:
                data = json.loads(line)
                token = data.get("response", "")
                if token:
                    yield token
                if data.get("done"):
                    break
    except Exception as e:
        yield f"\n[Error: {e}]"


def reset_instances():
    global _power_llm, _fast_llm, _embed_instance, _last_health_check, _last_health_time
    _power_llm = None
    _fast_llm = None
    _embed_instance = None
    _last_health_check = None
    _last_health_time = 0
    logger.info("[LLM] All instances reset.")
