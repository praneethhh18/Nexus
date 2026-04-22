"""
RAG Vector Store — ChromaDB operations for document storage and retrieval.
Persistent storage in chroma_db/ folder.
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from loguru import logger

from config.settings import CHROMA_PATH

COLLECTION_NAME = "nexusagent_docs"

_client: Optional[chromadb.PersistentClient] = None
_collection = None


def _get_client():
    global _client
    if _client is None:
        Path(CHROMA_PATH).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(
            path=CHROMA_PATH,
            settings=Settings(anonymized_telemetry=False),
        )
        logger.info(f"[VectorStore] ChromaDB connected at '{CHROMA_PATH}'")
    return _client


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        logger.info(f"[VectorStore] Collection '{COLLECTION_NAME}' loaded ({_collection.count()} docs)")
    return _collection


def add_documents(
    texts: List[str],
    embeddings: List[List[float]],
    metadatas: List[Dict[str, Any]],
    ids: Optional[List[str]] = None,
) -> int:
    """
    Add documents to the ChromaDB collection.
    Skips documents from a source that is already present.
    Returns number of documents added.
    """
    if not texts:
        return 0

    collection = _get_collection()

    # Deduplicate by source filename — skip if already loaded
    existing_sources: set = set()
    try:
        existing = collection.get(include=["metadatas"])
        for meta in existing["metadatas"]:
            if meta and "source" in meta:
                existing_sources.add(meta["source"])
    except Exception:
        pass

    new_texts, new_embeddings, new_metadatas, new_ids = [], [], [], []
    for i, (text, emb, meta) in enumerate(zip(texts, embeddings, metadatas)):
        source = meta.get("source", "unknown")
        if source in existing_sources:
            continue  # already loaded
        doc_id = ids[i] if ids else f"doc_{source}_{meta.get('page', 0)}_{meta.get('chunk_index', i)}"
        new_texts.append(text)
        new_embeddings.append(emb)
        new_metadatas.append(meta)
        new_ids.append(doc_id)

    if not new_texts:
        logger.info("[VectorStore] All documents already in store. Skipping.")
        return 0

    # Batch add (ChromaDB handles large batches fine)
    collection.add(
        documents=new_texts,
        embeddings=new_embeddings,
        metadatas=new_metadatas,
        ids=new_ids,
    )
    logger.success(f"[VectorStore] Added {len(new_texts)} chunks to collection.")
    return len(new_texts)


def search(
    query_embedding: List[float],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Search for top_k most similar documents.
    Returns list of dicts with: text, metadata, distance.
    """
    collection = _get_collection()
    count = collection.count()
    if count == 0:
        logger.warning("[VectorStore] Collection is empty. No results.")
        return []

    top_k = min(top_k, count)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
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


def delete_collection():
    """Remove and recreate the collection (full reset)."""
    global _collection
    client = _get_client()
    try:
        client.delete_collection(COLLECTION_NAME)
        logger.info(f"[VectorStore] Collection '{COLLECTION_NAME}' deleted.")
    except Exception:
        pass
    _collection = None
    _get_collection()


def get_collection_stats() -> Dict[str, Any]:
    """Return document count and collection name."""
    collection = _get_collection()
    count = collection.count()
    return {
        "collection_name": COLLECTION_NAME,
        "document_count": count,
        "chroma_path": CHROMA_PATH,
    }
