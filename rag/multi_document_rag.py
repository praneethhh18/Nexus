"""
Multi-Document RAG with Cross-Source Reasoning.
Supports:
  - Named source tracking — knows which answer came from which file
  - Cross-document comparison — "Compare what Q2 report says vs Q3 report on margins"
  - Contradiction detection — "Find contradictions between the sales policy and the HR policy"
  - Multi-source synthesis — reasons across multiple documents simultaneously
"""
from __future__ import annotations

import re
from typing import Dict, Any, List, Optional
from collections import defaultdict

from loguru import logger

from rag.embedder import embed_query
from rag.vector_store import search as vector_search, _get_collection
from config.settings import TOP_K_RETRIEVAL
from config.llm_config import get_llm


# ── Intent classification for multi-document queries ─────────────────────────
MULTI_DOC_KEYWORDS = {
    "compare", "versus", "vs", "difference", "between",
    "contradict", "conflict", "disagree", "differ",
    "both", "each", "all", "across",
}

COMPARISON_PATTERNS = [
    r"compare\s+(?:the\s+)?(?:.*?)(?:\s+(?:and|vs|versus|with|to))\s+(?:the\s+)?(.*?)\s+(?:on|about|regarding|for)?\s*(.*)",
    r"(?:what (?:does|do)|how (?:does|do)).*?(?:in|from|of)\s+(.*?)\s+(?:and|vs|versus|with)\s+(.*)",
    r"(?:difference|differ|contradict|conflict).*?(?:between|in)\s+(.*?)\s+(?:and|vs|versus|with)\s+(.*)",
]


def _is_multi_document_query(query: str) -> bool:
    """Detect if the query needs reasoning across multiple documents."""
    lower = query.lower()
    if any(kw in lower for kw in MULTI_DOC_KEYWORDS):
        return True
    for pattern in COMPARISON_PATTERNS:
        if re.search(pattern, lower):
            return True
    # Check for explicit source mentions: "in the Q2 report" and "in the Q3 report"
    source_mentions = re.findall(r"(?:in|from|the)\s+([\w\s]+?)\s+(?:report|doc|policy|file|document)", lower)
    if len(source_mentions) >= 2:
        return True
    return False


def _parse_comparison_query(query: str) -> Dict[str, str]:
    """Extract comparison targets from a query.
    Returns {doc_a, doc_b, topic}.
    """
    lower = query.lower()
    result = {"doc_a": None, "doc_b": None, "topic": query}

    for pattern in COMPARISON_PATTERNS:
        match = re.search(pattern, lower)
        if match:
            groups = match.groups()
            result["doc_a"] = groups[0].strip() if len(groups) > 0 else None
            result["doc_b"] = groups[1].strip() if len(groups) > 1 else None
            if len(groups) > 2 and groups[2].strip():
                result["topic"] = groups[2].strip()
            break

    # Try to extract source names
    source_pattern = r"(?:in|from|the)\s+([\w\s]+?)\s+(?:report|doc|policy|file|document)"
    mentions = re.findall(source_pattern, lower)
    if len(mentions) >= 2:
        result["doc_a"] = mentions[0].strip()
        result["doc_b"] = mentions[1].strip()

    return result


# ── Source-aware retrieval ───────────────────────────────────────────────────
def _get_available_sources() -> List[str]:
    """Get a list of all document sources in the vector store."""
    try:
        collection = _get_collection()
        existing = collection.get(include=["metadatas"])
        sources = set()
        for meta in existing.get("metadatas", []):
            if meta and "source" in meta:
                sources.add(meta["source"])
        return sorted(sources)
    except Exception as e:
        logger.error(f"[MultiDocRAG] Failed to get sources: {e}")
        return []


def _search_by_source(query_embedding: List[float], source_name: str,
                      top_k: int = 5) -> List[Dict[str, Any]]:
    """Search for results from a specific source document."""
    try:
        collection = _get_collection()
        count = collection.count()
        if count == 0:
            return []

        # Search with filter
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, count),
            include=["documents", "metadatas", "distances"],
            where={"source": source_name},
        )

        output = []
        docs = results.get("documents", [[]])[0]
        metas = results.get("metadatas", [[]])[0]
        dists = results.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs, metas, dists):
            output.append({
                "text": doc,
                "metadata": meta or {},
                "distance": float(dist),
            })
        return output
    except Exception as e:
        logger.warning(f"[MultiDocRAG] Source-filter search failed for '{source_name}': {e}")
        return []


def _distance_to_confidence(distance: float) -> float:
    """Convert ChromaDB cosine distance to 0-1 confidence score."""
    similarity = max(0.0, 1.0 - distance / 2.0)
    return round(similarity, 4)


def _retrieve_per_source(query: str, sources: List[str],
                          top_k_per_source: int = 5) -> Dict[str, List[Dict[str, Any]]]:
    """Retrieve relevant chunks from each specified source."""
    try:
        q_embedding = embed_query(query)
    except Exception as e:
        logger.error(f"[MultiDocRAG] Embedding failed: {e}")
        return {s: [] for s in sources}

    results = {}
    for source in sources:
        raw = _search_by_source(q_embedding, source, top_k_per_source)
        for r in raw:
            r["confidence"] = _distance_to_confidence(r["distance"])
        results[source] = raw[:top_k_per_source]
        logger.debug(f"[MultiDocRAG] Source '{source}': {len(results[source])} chunks")
    return results


def _deduplicate_chunks(chunks: List[Dict[str, Any]], similarity_threshold: float = 0.85) -> List[Dict[str, Any]]:
    """Remove near-duplicate chunks based on text overlap."""
    if not chunks:
        return chunks

    unique = [chunks[0]]
    for chunk in chunks[1:]:
        is_dup = False
        chunk_words = set(chunk["text"].lower().split())
        for existing in unique:
            existing_words = set(existing["text"].lower().split())
            if not chunk_words or not existing_words:
                continue
            overlap = len(chunk_words & existing_words) / max(len(chunk_words), len(existing_words))
            if overlap > similarity_threshold:
                is_dup = True
                break
        if not is_dup:
            unique.append(chunk)

    return unique


def _retrieve_all_grouped(query: str, top_k: int = 10) -> Dict[str, List[Dict[str, Any]]]:
    """Retrieve top_k results, deduplicate, and group them by source."""
    try:
        q_embedding = embed_query(query)
    except Exception as e:
        logger.error(f"[MultiDocRAG] Embedding failed: {e}")
        return {}

    raw_results = vector_search(q_embedding, top_k=top_k)
    grouped = defaultdict(list)

    for r in raw_results:
        source = r.get("metadata", {}).get("source", "Unknown")
        r["confidence"] = _distance_to_confidence(r["distance"])
        grouped[source].append({
            "text": r["text"],
            "metadata": r.get("metadata", {}),
            "distance": r["distance"],
            "confidence": r["confidence"],
        })

    # Deduplicate within each source
    for source in grouped:
        grouped[source] = _deduplicate_chunks(grouped[source])

    return dict(grouped)


# ── Cross-document reasoning ─────────────────────────────────────────────────
def _compare_documents(query: str, doc_a: str, doc_b: str,
                       topic: str) -> Dict[str, Any]:
    """Compare what two documents say about a specific topic."""
    sources = _get_available_sources()

    # Try to match doc names to actual sources
    source_a = _match_source(doc_a, sources) if doc_a else None
    source_b = _match_source(doc_b, sources) if doc_b else None

    if not source_a and not source_b:
        # Fall back to general retrieval
        grouped = _retrieve_all_grouped(query, top_k=10)
        return _cross_source_synthesize(query, grouped, "comparison")

    # Retrieve from each source
    search_query = f"{topic} {query}" if topic != query else query
    per_source = _retrieve_per_source(search_query,
                                       [s for s in [source_a, source_b] if s],
                                       top_k_per_source=5)

    return _cross_source_synthesize(query, per_source, "comparison",
                                     doc_a=source_a, doc_b=source_b, topic=topic)


def _detect_contradictions(query: str) -> Dict[str, Any]:
    """Find contradictions across documents."""
    sources = _get_available_sources()
    if len(sources) < 2:
        return {
            "answer": "I need at least 2 documents in the knowledge base to find contradictions. "
                      f"Currently there are {len(sources)} document(s).",
            "contradictions": [],
            "sources_used": sources,
        }

    # Retrieve broadly to get content from all sources
    grouped = _retrieve_all_grouped(query, top_k=20)

    # Build context for LLM
    context_parts = []
    for source, chunks in grouped.items():
        chunk_texts = "\n---\n".join(
            f"[p.{c['metadata'].get('page', '?')}] {c['text'][:500]}" for c in chunks[:5]
        )
        context_parts.append(f"### {source}\n{chunk_texts}")

    context = "\n\n".join(context_parts)

    try:
        llm = get_llm()
        prompt = f"""You are analyzing multiple of documents for contradictions.

Identify any contradictory statements across these documents.
A contradiction is when two documents say opposite or conflicting things about the same topic.

DOCUMENTS:
{context[:6000]}

List each contradiction found (if any) in this format:
1. TOPIC: <topic>
   DOC A says: <statement from doc A>
   DOC B says: <statement from doc B>
   Nature of contradiction: <explain the conflict>

If no contradictions found, say "No contradictions found."

CONTRADICTIONS:"""

        response = llm.invoke(prompt)

        # Parse contradictions
        contradictions = []
        current = {}
        for line in response.strip().split("\n"):
            line = line.strip()
            if line.startswith("1.") or re.match(r"^\d+\.", line):
                if current:
                    contradictions.append(current)
                current = {"topic": line.split(":", 1)[1].strip() if ":" in line else line}
            elif "TOPIC:" in line.upper():
                current["topic"] = line.split(":", 1)[1].strip()
            elif "DOC A" in line.upper() or "SAYS:" in line.upper():
                key = "statement_a" if "A" in line.upper() else "statement_b"
                current[key] = line.split(":", 1)[1].strip() if ":" in line else line
            elif "NATURE" in line.upper():
                current["explanation"] = line.split(":", 1)[1].strip() if ":" in line else line

        if current:
            contradictions.append(current)

        return {
            "answer": response.strip(),
            "contradictions": contradictions,
            "sources_used": list(grouped.keys()),
        }
    except Exception as e:
        logger.error(f"[MultiDocRAG] Contradiction detection failed: {e}")
        return {
            "answer": f"I encountered an error analyzing contradictions: {e}",
            "contradictions": [],
            "sources_used": list(grouped.keys()),
        }


def _match_source(hint: str, available_sources: List[str]) -> Optional[str]:
    """Fuzzy-match a user-provided document name to an actual source.
    Uses multiple strategies: exact, substring, token overlap, and character n-gram similarity.
    """
    if not hint:
        return None
    hint_lower = hint.lower().strip()

    # 1. Exact match
    for s in available_sources:
        if hint_lower == s.lower():
            return s

    # 2. Substring match (either direction)
    for s in available_sources:
        if hint_lower in s.lower() or s.lower() in hint_lower:
            return s

    # 3. Filename stem match (strip extension and path)
    hint_clean = hint_lower.replace("_", " ").replace("-", " ").replace(".", " ")
    for s in available_sources:
        s_clean = s.lower().rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        s_clean = s_clean.rsplit(".", 1)[0].replace("_", " ").replace("-", " ")
        if hint_clean in s_clean or s_clean in hint_clean:
            return s

    # 4. Token overlap with normalized scoring
    hint_tokens = set(hint_clean.split())
    best_score = 0
    best_match = None
    for s in available_sources:
        s_clean = s.lower().replace("_", " ").replace("-", " ").replace(".", " ")
        s_tokens = set(s_clean.split())
        if not hint_tokens or not s_tokens:
            continue
        overlap = len(hint_tokens & s_tokens)
        # Jaccard similarity
        union = len(hint_tokens | s_tokens)
        score = overlap / union if union > 0 else 0
        if score > best_score:
            best_score = score
            best_match = s

    return best_match if best_score > 0.2 else None


def _cross_source_synthesize(query: str,
                              grouped_results: Dict[str, List[Dict[str, Any]]],
                              mode: str = "general",
                              **kwargs) -> Dict[str, Any]:
    """Synthesize an answer using content from multiple sources."""
    if not grouped_results:
        return {
            "answer": "No relevant documents found. Please upload documents first.",
            "sources_used": [],
            "per_source_summaries": {},
            "citations": [],
            "mode": mode,
        }

    # Build structured context
    context_parts = []
    all_citations = []
    per_source_summaries = {}

    for source, chunks in grouped_results.items():
        chunk_texts = "\n---\n".join(
            f"[p.{c['metadata'].get('page', '?')}] {c['text'][:500]}" for c in chunks[:5]
        )
        context_parts.append(f"### DOCUMENT: {source}\n{chunk_texts}")

        # Build per-source summary
        try:
            llm = get_llm()
            summary_prompt = f"Summarize what this document says in 2-3 sentences:\n\n{chunk_texts[:2000]}"
            summary = llm.invoke(summary_prompt).strip()
            per_source_summaries[source] = summary
        except Exception:
            per_source_summaries[source] = f"{len(chunks)} relevant chunks found."

        for c in chunks[:3]:
            all_citations.append({
                "source": source,
                "page": c["metadata"].get("page", "?"),
                "confidence": c.get("confidence", 0),
            })

    context = "\n\n".join(context_parts)

    # Build synthesis prompt based on mode
    if mode == "comparison":
        doc_a = kwargs.get("doc_a", "")
        doc_b = kwargs.get("doc_b", "")
        topic = kwargs.get("topic", query)
        synthesis_prompt = (
            f"Compare and contrast what the following documents say about: {topic}\n\n"
            f"DOCUMENTS AND CONTENT:\n{context[:6000]}\n\n"
            f"Provide a structured comparison:\n"
            f"1. What {doc_a or 'Document A'} says\n"
            f"2. What {doc_b or 'Document B'} says\n"
            f"3. Key similarities\n"
            f"4. Key differences\n\n"
            f"Be specific and cite which document each point comes from."
        )
    elif mode == "contradiction":
        synthesis_prompt = (
            f"Analyze the following documents for contradictions and conflicting statements:\n\n"
            f"{context[:6000]}\n\n"
            f"Identify contradictions, explain the nature of each conflict, "
            f"and suggest which document might be more authoritative."
        )
    else:
        synthesis_prompt = (
            f"Answer the following question using information from ALL available documents:\n\n"
            f"QUESTION: {query}\n\n"
            f"DOCUMENTS AND CONTENT:\n{context[:6000]}\n\n"
            f"Provide a comprehensive answer that synthesizes information from all sources. "
            f"Clearly indicate which document each piece of information comes from."
        )

    try:
        llm = get_llm()
        answer = llm.invoke(synthesis_prompt).strip()
    except Exception as e:
        logger.error(f"[MultiDocRAG] Synthesis failed: {e}")
        answer = f"Error synthesizing multi-document answer: {e}"

    return {
        "answer": answer,
        "sources_used": list(grouped_results.keys()),
        "per_source_summaries": per_source_summaries,
        "citations": all_citations,
        "mode": mode,
    }


# ── Main entry point ─────────────────────────────────────────────────────────
def multi_doc_retrieve(query: str) -> Dict[str, Any]:
    """
    Full multi-document RAG pipeline.
    1. Detect if query needs cross-document reasoning
    2. Classify: comparison, contradiction, or general synthesis
    3. Retrieve from relevant sources
    4. Synthesize with source attribution

    Returns:
        {
          answer: str,
          sources_used: List[str],
          per_source_summaries: Dict[str, str],
          citations: List[dict],
          mode: str,
          contradictions: List[dict] (only for contradiction mode),
          is_multi_doc: bool,
        }
    """
    sources = _get_available_sources()
    if not sources:
        return {
            "answer": "No documents in the knowledge base. Please upload documents first.",
            "sources_used": [],
            "per_source_summaries": {},
            "citations": [],
            "mode": "empty",
            "is_multi_doc": False,
        }

    is_multi = _is_multi_document_query(query)

    if not is_multi:
        # Single-doc or general query — use standard retrieval but still track sources
        grouped = _retrieve_all_grouped(query, top_k=TOP_K_RETRIEVAL)
        if len(grouped) >= 2:
            # Multiple sources found — still do cross-source synthesis
            result = _cross_source_synthesize(query, grouped, mode="general")
            result["is_multi_doc"] = True
            return result
        else:
            # Single source — simple synthesis
            result = _cross_source_synthesize(query, grouped, mode="general")
            result["is_multi_doc"] = False
            return result

    # Multi-document query — classify intent
    lower = query.lower()

    if any(kw in lower for kw in ("contradict", "conflict", "disagree", "differ")):
        result = _detect_contradictions(query)
        result["is_multi_doc"] = True
        return result

    if any(kw in lower for kw in ("compare", "versus", "vs", "difference", "between")):
        parsed = _parse_comparison_query(query)
        result = _compare_documents(query, parsed["doc_a"], parsed["doc_b"], parsed["topic"])
        result["is_multi_doc"] = True
        return result

    # Default: general multi-source synthesis
    grouped = _retrieve_all_grouped(query, top_k=15)
    result = _cross_source_synthesize(query, grouped, mode="general")
    result["is_multi_doc"] = True
    return result


def get_sources_list() -> List[Dict[str, Any]]:
    """Get metadata about all available document sources."""
    try:
        collection = _get_collection()
        existing = collection.get(include=["metadatas"])
        source_info = defaultdict(lambda: {"chunk_count": 0, "pages": set(), "file_type": "unknown"})

        for meta in existing.get("metadatas", []):
            if meta and "source" in meta:
                src = meta["source"]
                source_info[src]["chunk_count"] += 1
                if "page" in meta:
                    source_info[src]["pages"].add(meta["page"])
                if "file_type" in meta:
                    source_info[src]["file_type"] = meta["file_type"]

        return [
            {
                "name": name,
                "chunk_count": info["chunk_count"],
                "page_count": len(info["pages"]),
                "file_type": info["file_type"],
            }
            for name, info in sorted(source_info.items())
        ]
    except Exception as e:
        logger.error(f"[MultiDocRAG] get_sources_list failed: {e}")
        return []
