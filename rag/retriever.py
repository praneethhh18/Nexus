"""
RAG Retriever — query → embed → search → rerank → citations.
Uses local Ollama for reranking; no external API calls.
"""
from __future__ import annotations

from typing import List, Dict, Any

from loguru import logger

from config.settings import TOP_K_RETRIEVAL
from rag.embedder import embed_query
from rag.vector_store import search


_LOW_CONFIDENCE_THRESHOLD = 0.40


def _distance_to_confidence(distance: float) -> float:
    """Convert ChromaDB cosine distance (0=identical, 2=opposite) to a 0-1 confidence score."""
    # cosine distance in [0, 2]; similarity = 1 - distance/2
    similarity = max(0.0, 1.0 - distance / 2.0)
    return round(similarity, 4)


def _rerank_with_llm(query: str, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Ask the local LLM to pick the 3 most relevant chunks from the top 5.
    Returns candidates sorted by LLM relevance score (best first).
    Falls back to original order on any error.
    """
    try:
        from config.llm_config import get_llm
        llm = get_llm()

        numbered = "\n\n".join(
            f"[{i+1}] Source: {c['metadata'].get('source','?')} p.{c['metadata'].get('page','?')}\n{c['text'][:400]}"
            for i, c in enumerate(candidates)
        )
        prompt = (
            f"Given the question: \"{query}\"\n\n"
            f"Rate each passage 1-10 for relevance. Reply ONLY with a comma-separated list of scores "
            f"in order (e.g. 8,3,9,4,7). {len(candidates)} passages:\n\n{numbered}"
        )
        response = llm.invoke(prompt)

        # Parse scores
        import re
        scores_raw = re.findall(r"\d+", response)
        scores = [int(s) for s in scores_raw[: len(candidates)]]
        if len(scores) != len(candidates):
            return candidates  # fallback

        scored = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        reranked = [c for c, _ in scored[:3]]
        logger.debug(f"[Retriever] Reranked scores: {scores}")
        return reranked
    except Exception as e:
        logger.warning(f"[Retriever] LLM rerank failed (using original order): {e}")
        return candidates[:3]


def retrieve(query: str, top_k: int = None) -> Dict[str, Any]:
    """
    Full retrieval pipeline:
    1. Embed the query
    2. Search ChromaDB for top_k candidates
    3. Rerank with local LLM, return top 3
    4. Return results with confidence scores and citations

    Returns:
        {
          results: [{text, source, page, confidence, rank}],
          low_confidence: bool,
          warning: str | None,
          query: str
        }
    """
    if top_k is None:
        top_k = TOP_K_RETRIEVAL

    # 1. Embed
    try:
        q_embedding = embed_query(query)
    except Exception as e:
        return {
            "results": [],
            "low_confidence": True,
            "warning": f"Embedding failed: {e}",
            "query": query,
        }

    # 2. Search
    raw_results = search(q_embedding, top_k=max(top_k, 5))
    if not raw_results:
        return {
            "results": [],
            "low_confidence": True,
            "warning": "No documents found in the knowledge base. Please upload documents first.",
            "query": query,
        }

    # Attach confidence scores
    for r in raw_results:
        r["confidence"] = _distance_to_confidence(r["distance"])

    # 3. Rerank (pick best 3 from top 5)
    reranked = _rerank_with_llm(query, raw_results[:5])

    # 4. Format output
    formatted = []
    for rank, r in enumerate(reranked, start=1):
        meta = r.get("metadata", {})
        formatted.append({
            "text": r["text"],
            "source": meta.get("source", "Unknown"),
            "page": meta.get("page", "?"),
            "confidence": r["confidence"],
            "rank": rank,
        })

    top_confidence = formatted[0]["confidence"] if formatted else 0.0
    low_confidence = top_confidence < _LOW_CONFIDENCE_THRESHOLD

    warning = None
    if low_confidence:
        warning = (
            f"Low confidence ({top_confidence:.0%}) — answer may not be accurate. "
            "Consider uploading more relevant documents."
        )

    logger.info(
        f"[Retriever] Query: '{query[:60]}' → {len(formatted)} results, "
        f"top confidence: {top_confidence:.0%}"
    )

    return {
        "results": formatted,
        "low_confidence": low_confidence,
        "warning": warning,
        "query": query,
    }
