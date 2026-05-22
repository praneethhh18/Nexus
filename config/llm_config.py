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


class _CloudLLMShim:
    """Drop-in stand-in for an Ollama LangChain LLM when Ollama is down.

    Exposes the two methods callers actually use (`.invoke(prompt)` and
    `__call__(prompt)`), and dispatches to `config.llm_provider.invoke`
    which already knows how to talk to Bedrock / NIM / Groq with the
    same fallback budget. Without this shim, every code path that
    requires `get_llm()` (PlannerAgent, RAG synthesizer, report
    generation, what-if, memory deep-learn, workflow AI nodes) hard-
    crashes the moment Ollama isn't running locally."""
    __slots__ = ("_temperature",)

    def __init__(self, temperature: float):
        self._temperature = temperature

    def _call(self, prompt: str) -> str:
        from config.llm_provider import invoke as _provider_invoke
        return _provider_invoke(
            prompt, system="", max_tokens=1024,
            temperature=self._temperature, fast=False,
        )

    def invoke(self, prompt: str) -> str:
        return self._call(prompt)

    def __call__(self, prompt: str) -> str:
        return self._call(prompt)


def get_llm(temperature: float = 0.1):
    """Return the POWER model (8B) for SQL, RAG, reports, synthesis.

    Tries local Ollama first (faster + free); falls back to a cloud
    shim that hits whatever provider is configured (Bedrock / NIM /
    Groq) when Ollama isn't running. Previously raised RuntimeError
    when Ollama was down, which 500'd every report/synthesis path."""
    global _power_llm
    if _power_llm is not None:
        return _power_llm

    healthy, _ = health_check(force=True)
    if not healthy:
        # One retry, then fall back to the cloud provider rather than
        # crashing every caller. Cloud is what the chat flow already
        # uses successfully, so reports/RAG/etc. should follow suit.
        time.sleep(1)
        healthy, _ = health_check(force=True)
        if not healthy:
            logger.warning(
                "[LLM] Ollama not reachable, falling back to cloud "
                "provider via llm_provider.invoke (Bedrock/NIM/Groq)."
            )
            _power_llm = _CloudLLMShim(temperature)
            return _power_llm

    chosen = OLLAMA_MODEL
    if not _model_available(OLLAMA_MODEL):
        chosen = OLLAMA_FALLBACK_MODEL

    logger.info(f"[LLM] Loading power model: {chosen}")
    _power_llm = Ollama(base_url=OLLAMA_BASE_URL, model=chosen, temperature=temperature)
    logger.success(f"[LLM] Power model '{chosen}' ready.")
    return _power_llm


def get_fast_llm(temperature: float = 0.1):
    """Return the FAST model (1.5-3B) for chat, classification, intent detection.
    Same Ollama-then-cloud fallback as get_llm()."""
    global _fast_llm
    if _fast_llm is not None:
        return _fast_llm

    healthy, _ = health_check(force=True)
    if not healthy:
        logger.warning(
            "[LLM] Ollama not reachable for fast model, using cloud "
            "shim (Bedrock fast tier / Nova Lite)."
        )
        # Use the same shim, but the underlying invoke can prefer fast tier.
        class _FastShim(_CloudLLMShim):
            def _call(self, prompt: str) -> str:
                from config.llm_provider import invoke as _pi
                return _pi(prompt, system="", max_tokens=512,
                           temperature=self._temperature, fast=True)
        _fast_llm = _FastShim(temperature)
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
