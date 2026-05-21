"""
RAG Embedder — dual backend (Ollama / Bedrock Titan) with the same
privacy kill-switch the LLM router uses.

Routing precedence (mirrors config.llm_provider.invoke):
    1. sensitive=True              → Ollama (never leaves the machine)
    2. ALLOW_CLOUD_LLM=false       → Ollama (kill switch)
    3. EMBED_BACKEND=ollama        → Ollama (explicit pin)
    4. EMBED_BACKEND=bedrock       → Bedrock Titan v2
    5. EMBED_BACKEND=auto (default):
         - Bedrock Titan if AWS creds present + boto3 installed
         - Else Ollama

Either backend produces a `list[list[float]]`. Vector dimensions differ
(nomic = 768, titan v2 = 1024) but Chroma is told the dim at collection
creation time, so a workspace MUST stick to one backend per collection.
A switch invalidates existing embeddings — re-index from Documents.

Why this lives in one file:
- Single chokepoint, easy to audit
- Mirrors `config.llm_provider`'s shape so callers (rag.vector_store,
  api.knowledge.upload) get a familiar API
- No new top-level dependency — boto3 is already pulled in by Bedrock LLM
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional

import numpy as np
from loguru import logger

from config.settings import OLLAMA_BASE_URL, EMBED_MODEL
from config import privacy

# Concurrent Bedrock calls. Titan v2 doesn't have a batch endpoint, so we
# fan out N requests in parallel. 8 is a safe default — well under the
# 50 RPS quota a fresh Bedrock account gets, and big enough that a 200-
# chunk PDF embeds in ~5s instead of ~80s. Tune via env if needed.
BEDROCK_EMBED_WORKERS = int(os.getenv("BEDROCK_EMBED_WORKERS", "4") or 4)

# Cached client handles — populated lazily on first call to each backend.
_ollama_embedder = None
_bedrock_client = None


# ── Backend selection ────────────────────────────────────────────────────────
def _resolve_backend(sensitive: bool) -> str:
    """Return 'ollama' or 'bedrock'. See module docstring for rules."""
    if sensitive:
        return "ollama"
    if not privacy.ALLOW_CLOUD_LLM:
        return "ollama"

    pin = (os.getenv("EMBED_BACKEND") or "auto").strip().lower()
    if pin == "ollama":
        return "ollama"
    if pin == "bedrock":
        return "bedrock"

    # auto: prefer Bedrock if creds present (matches LLM router's bias toward
    # cloud when configured) — kept in lockstep so admins managing one set of
    # creds get both LLM and embeddings on the same backend.
    try:
        from config.llm_bedrock import bedrock_available
        if bedrock_available():
            return "bedrock"
    except Exception:
        pass
    return "ollama"


def active_backend() -> str:
    """Read the current default routing (no per-call overrides)."""
    return _resolve_backend(sensitive=False)


# ── Ollama backend ───────────────────────────────────────────────────────────
def _get_ollama():
    global _ollama_embedder
    if _ollama_embedder is None:
        from langchain_ollama import OllamaEmbeddings
        logger.info(f"[Embedder/Ollama] Loading '{EMBED_MODEL}' from {OLLAMA_BASE_URL}…")
        _ollama_embedder = OllamaEmbeddings(
            base_url=OLLAMA_BASE_URL,
            model=EMBED_MODEL,
        )
        logger.success(f"[Embedder/Ollama] '{EMBED_MODEL}' ready.")
    return _ollama_embedder


def _embed_ollama_docs(texts: List[str]) -> List[List[float]]:
    return _get_ollama().embed_documents(texts)


def _embed_ollama_query(text: str) -> List[float]:
    return _get_ollama().embed_query(text)


# ── Bedrock Titan backend ────────────────────────────────────────────────────
# Default model: Titan Text Embeddings v2 (1024 dim, ~₹0.01 per 1M tokens
# at the us-east-1 list price as of Q2-2026). Override with BEDROCK_EMBED_MODEL.
TITAN_MODEL = os.getenv("BEDROCK_EMBED_MODEL", "amazon.titan-embed-text-v2:0")


def _get_bedrock():
    global _bedrock_client
    if _bedrock_client is None:
        from config.llm_bedrock import _get_client as _bedrock_get_client
        _bedrock_client = _bedrock_get_client()
        logger.success(f"[Embedder/Bedrock] using model {TITAN_MODEL}")
    return _bedrock_client


def _embed_bedrock_one(text: str, _max_retries: int = 6) -> List[float]:
    """One Titan call → one vector. Titan v2 doesn't have a batch endpoint,
    so we serialise. Caller can parallelise if throughput matters later.

    Bedrock returns ThrottlingException when the parallel-fanout from
    _embed_bedrock_docs sends more requests/sec than the account quota
    allows (often the case for new accounts with lower TPM limits).
    Without backoff, a 60-chunk PDF would fail half its calls. With this
    exponential backoff retry, we keep latency reasonable while staying
    inside the quota."""
    import time
    import random
    client = _get_bedrock()
    body = json.dumps({"inputText": text})
    delay = 0.5
    for attempt in range(_max_retries):
        try:
            resp = client.invoke_model(
                modelId=TITAN_MODEL,
                body=body,
                contentType="application/json",
                accept="application/json",
            )
            payload = json.loads(resp["body"].read())
            return payload["embedding"]
        except Exception as e:
            # Catch any throttling-shaped error (ThrottlingException,
            # ProvisionedThroughputExceededException, even ConnectionError).
            msg = str(e).lower()
            throttled = ("throttl" in msg or "too many requests" in msg
                         or "rate exceed" in msg or "provisioned" in msg)
            if not throttled or attempt == _max_retries - 1:
                raise
            sleep_for = min(8.0, delay + random.uniform(0, 0.25))
            logger.warning(f"[Embedder/Bedrock] throttled (attempt {attempt+1}/{_max_retries}) — sleeping {sleep_for:.1f}s")
            time.sleep(sleep_for)
            delay *= 2  # exponential backoff
    # Unreachable, but keeps type-checkers happy.
    raise RuntimeError("Bedrock embed exhausted retries")


def _embed_bedrock_docs(texts: List[str]) -> List[List[float]]:
    """Parallel-embed N texts via Bedrock Titan.

    Titan has no batch endpoint, so a 200-chunk PDF was hitting 200
    serial invoke_model calls (~80s end-to-end). Fanning out 8 in
    parallel cuts that to ~10s without tripping the default Bedrock
    rate quota.

    Order is preserved — output[i] corresponds to texts[i] regardless of
    which thread finished first."""
    # Redact PII before each call. Documents uploaded by the user are
    # less sensitive than chat prompts (the user CHOSE to share them)
    # but redaction is cheap insurance against unexpected secrets.
    prepped = [privacy.prepare_for_cloud(t, "")[0] for t in texts]
    n = len(prepped)
    out: List[Optional[List[float]]] = [None] * n
    workers = max(1, min(BEDROCK_EMBED_WORKERS, n))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_embed_bedrock_one, prepped[i]): i for i in range(n)}
        for fut in as_completed(futures):
            i = futures[fut]
            out[i] = fut.result()
    return [v for v in out if v is not None]  # type: ignore[return-value]


def _embed_bedrock_query(text: str) -> List[float]:
    red, _, _ = privacy.prepare_for_cloud(text, "")
    return _embed_bedrock_one(red)


# ── Public API (matches old signatures so callers don't change) ─────────────
def embed_documents(texts: List[str], sensitive: bool = False) -> List[List[float]]:
    """
    Embed a list of document texts. Returns one vector per input.

    sensitive=True forces local Ollama even if cloud is configured. Pass
    True when embedding anything you would NOT want on AWS (DB rows with
    PII, customer messages, internal financials).

    Raises ConnectionError if the selected backend is unreachable. Callers
    can catch this to keep the file on disk without indexing — see
    api/server.py /api/knowledge/upload for the pattern.
    """
    if not texts:
        return []
    backend = _resolve_backend(sensitive)
    try:
        if backend == "bedrock":
            vectors = _embed_bedrock_docs(texts)
        else:
            vectors = _embed_ollama_docs(texts)
        logger.debug(f"[Embedder] {backend} → {len(texts)} doc(s) embedded.")
        return vectors
    except ConnectionError:
        # Re-raise so the upload route can show "Ollama offline" without
        # touching a 500. Don't silently switch backends — vector dims
        # change between providers and would corrupt the collection.
        raise
    except Exception as e:
        logger.error(f"[Embedder/{backend}] embed_documents failed: {e}")
        raise


def embed_query(query: str, sensitive: bool = False) -> List[float]:
    """Embed a single query string. Same routing as embed_documents."""
    backend = _resolve_backend(sensitive)
    try:
        if backend == "bedrock":
            vector = _embed_bedrock_query(query)
        else:
            vector = _embed_ollama_query(query)
        logger.debug(f"[Embedder] {backend} → query embedded: '{query[:60]}…'")
        return vector
    except Exception as e:
        logger.error(f"[Embedder/{backend}] embed_query failed: {e}")
        raise


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
