"""
RAG Embedder — wraps Ollama nomic-embed-text for document and query embedding.
Uses the local Ollama instance; no external API calls.
"""
from __future__ import annotations

from typing import List
import numpy as np
from loguru import logger

from config.settings import OLLAMA_BASE_URL, EMBED_MODEL

_embedder_instance = None


def _get_embedder():
    """Lazy-load and cache the Ollama embedding client."""
    global _embedder_instance
    if _embedder_instance is None:
        from langchain_ollama import OllamaEmbeddings
        logger.info(f"[Embedder] Loading '{EMBED_MODEL}' from Ollama…")
        _embedder_instance = OllamaEmbeddings(
            base_url=OLLAMA_BASE_URL,
            model=EMBED_MODEL,
        )
        logger.success(f"[Embedder] '{EMBED_MODEL}' ready.")
    return _embedder_instance


def embed_documents(texts: List[str]) -> List[List[float]]:
    """
    Embed a list of document texts.
    Returns a list of float vectors (one per text).
    """
    if not texts:
        return []
    try:
        embedder = _get_embedder()
        vectors = embedder.embed_documents(texts)
        logger.debug(f"[Embedder] Embedded {len(texts)} documents.")
        return vectors
    except Exception as e:
        logger.error(f"[Embedder] embed_documents failed: {e}")
        raise


def embed_query(query: str) -> List[float]:
    """
    Embed a single query string.
    Returns a float vector.
    """
    try:
        embedder = _get_embedder()
        vector = embedder.embed_query(query)
        logger.debug(f"[Embedder] Query embedded: '{query[:60]}…'")
        return vector
    except Exception as e:
        logger.error(f"[Embedder] embed_query failed: {e}")
        raise


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two vectors."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    denom = np.linalg.norm(a) * np.linalg.norm(b)
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)
