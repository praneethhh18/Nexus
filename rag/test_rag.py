"""
RAG Test Script — generates a sample doc, ingests it, runs 3 test queries.
Run: python rag/test_rag.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger
from config.settings import ensure_directories, DOCUMENTS_DIR

TEST_QUERIES = [
    "What is the refund policy for enterprise clients?",
    "How many vacation days do employees get?",
    "What are the escalation procedures for critical issues?",
]

SAMPLE_POLICY = """
NEXUS CORP — COMPANY POLICY DOCUMENT

REFUND POLICY
Enterprise clients are eligible for a full refund within 30 days of purchase.
SMB clients receive a 14-day refund window. All refunds must be approved by the Finance team
and submitted via the internal portal. Refunds for professional services are non-refundable
once work has commenced. Exceptions require written approval from the VP of Sales.

LEAVE POLICY
Full-time employees receive 20 days of paid vacation annually.
Part-time employees receive 10 days. Sick leave is separate at 12 days per year.
Unused vacation rolls over up to a maximum of 5 days. All leave requests must be submitted
through the HR portal at least 3 business days in advance.

ESCALATION PROCEDURES
Critical issues (Severity 1) must be escalated to the Engineering Lead within 30 minutes.
Severity 2 issues require a response within 4 hours. For client-facing issues, the Account Manager
must be notified immediately. All escalations are tracked in the incident management system.
Post-incident reviews are mandatory for Severity 1 events within 48 hours.

DATA SECURITY
All customer data must be stored encrypted at rest (AES-256) and in transit (TLS 1.3).
Access to production databases requires two-factor authentication and is logged automatically.
Employees must not store customer PII on personal devices. Violations are subject to
disciplinary action up to and including termination.
"""


def main():
    ensure_directories()

    # Generate sample document if needed
    sample_path = Path(DOCUMENTS_DIR) / "company_policy_test.txt"
    if not sample_path.exists():
        sample_path.write_text(SAMPLE_POLICY, encoding="utf-8")
        logger.info(f"Created sample document: {sample_path}")

    # Ingest
    from rag.ingestion import ingest_file
    from rag.embedder import embed_documents
    from rag.vector_store import add_documents, get_collection_stats

    logger.info("Ingesting sample document…")
    docs = ingest_file(str(sample_path))
    logger.info(f"Got {len(docs)} chunks")

    texts = [d.page_content for d in docs]
    metas = [d.metadata for d in docs]
    embeddings = embed_documents(texts)
    added = add_documents(texts, embeddings, metas)
    stats = get_collection_stats()
    logger.info(f"Collection stats: {stats}")

    # Run test queries
    from rag.retriever import retrieve

    print("\n" + "="*60)
    print("RAG TEST — 3 QUERIES")
    print("="*60)

    all_passed = True
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"\nQuery {i}: {query}")
        result = retrieve(query, top_k=3)

        if result["warning"]:
            print(f"  WARNING: {result['warning']}")

        if not result["results"]:
            print("  FAIL — no results returned")
            all_passed = False
            continue

        top = result["results"][0]
        print(f"  Top result confidence: {top['confidence']:.0%}")
        print(f"  Source: {top['source']} (page {top['page']})")
        print(f"  Text snippet: {top['text'][:200]}…")
        print(f"  PASS" if top["confidence"] > 0.2 else "  WARN — low confidence")

    print("\n" + "="*60)
    print(f"RAG TEST {'PASSED' if all_passed else 'COMPLETED WITH WARNINGS'}")
    print("="*60)


if __name__ == "__main__":
    main()
