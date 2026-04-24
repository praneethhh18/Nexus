"""Tests for RAG collections, saved queries + templates, structured research."""
from __future__ import annotations

import importlib
import os
import sqlite3
import tempfile


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import documents as _docs
    importlib.reload(_docs)
    from api import rag_collections as _rc
    importlib.reload(_rc)
    from api import saved_queries as _sq
    importlib.reload(_sq)
    from agents import research_agent as _ra
    importlib.reload(_ra)
    _docs._get_conn().close()
    return _docs, _rc, _sq, _ra


def _insert_doc(db_path: str, business_id: str, doc_id: str, title: str = "Doc",
                collection_id=None, expires_at=None) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO nexus_documents "
            "(id, business_id, template_key, title, format, file_path, "
            " variables, created_at, created_by, collection_id, expires_at) "
            "VALUES (?, ?, 'seed', ?, 'pdf', '/tmp/x.pdf', '{}', ?, 'u', ?, ?)",
            (doc_id, business_id, title,
             __import__("datetime").datetime.utcnow().isoformat(),
             collection_id, expires_at),
        )
        conn.commit()
    finally:
        conn.close()


# ── RAG collections ─────────────────────────────────────────────────────────
def test_create_and_list_collection():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        c = rc.create_collection("biz-1", "HR policies")
        assert c["name"] == "HR policies"
        assert c["color"].startswith("#")
        listed = rc.list_collections("biz-1")
        assert len(listed) == 1
        assert listed[0]["document_count"] == 0


def test_collection_duplicate_returns_existing():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        a = rc.create_collection("biz-1", "Sales")
        b = rc.create_collection("biz-1", "sales")   # case-insensitive
        assert a["id"] == b["id"]


def test_assign_document_to_collection():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        col = rc.create_collection("biz-1", "Legal")
        _insert_doc(db, "biz-1", "doc-1", "Contract")
        rc.assign_document("biz-1", "doc-1", col["id"])
        docs = rc.list_documents_in_collection("biz-1", col["id"])
        assert len(docs) == 1
        assert docs[0]["id"] == "doc-1"


def test_assign_unknown_collection_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        _insert_doc(db, "biz-1", "doc-1")
        import pytest
        with pytest.raises(ValueError):
            rc.assign_document("biz-1", "doc-1", "col-does-not-exist")


def test_delete_collection_unassigns_docs():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        col = rc.create_collection("biz-1", "Temp")
        _insert_doc(db, "biz-1", "doc-1", collection_id=col["id"])
        rc.delete_collection("biz-1", col["id"])
        # Doc survives with NULL collection_id
        conn = sqlite3.connect(db)
        row = conn.execute(
            "SELECT collection_id FROM nexus_documents WHERE id = ?", ("doc-1",),
        ).fetchone()
        conn.close()
        assert row[0] is None


def test_set_and_clear_expiry():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        _insert_doc(db, "biz-1", "doc-1")
        rc.set_expiry("biz-1", "doc-1", "2020-01-01T00:00:00")
        stale = rc.stale_documents("biz-1")
        assert len(stale) == 1 and stale[0]["id"] == "doc-1"
        rc.set_expiry("biz-1", "doc-1", None)
        assert rc.stale_documents("biz-1") == []


def test_invalid_expiry_format_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        _insert_doc(db, "biz-1", "doc-1")
        import pytest
        with pytest.raises(ValueError):
            rc.set_expiry("biz-1", "doc-1", "not a date")


def test_collection_scoped_to_business():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        a = rc.create_collection("biz-a", "Shared")
        b = rc.create_collection("biz-b", "Shared")
        assert a["id"] != b["id"]
        assert len(rc.list_collections("biz-a")) == 1
        assert len(rc.list_collections("biz-b")) == 1


def test_reingest_clears_expiry():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, rc, _, _ = _fresh(db)
        _insert_doc(db, "biz-1", "doc-1", expires_at="2020-01-01T00:00:00")
        rc.mark_for_reingest("biz-1", "doc-1")
        assert rc.stale_documents("biz-1") == []


# ── Saved queries + templates ──────────────────────────────────────────────
def test_create_and_list_saved_query():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, sq, _ = _fresh(db)
        q = sq.create_query("biz-1", {
            "name": "Monthly revenue",
            "question": "show monthly revenue for the last year",
            "chart_type": "line",
        })
        assert q["name"] == "Monthly revenue"
        assert q["chart_type"] == "line"
        listed = sq.list_queries("biz-1")
        assert len(listed) == 1


def test_duplicate_query_name_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, sq, _ = _fresh(db)
        sq.create_query("biz-1", {"name": "X", "question": "?"})
        import pytest
        with pytest.raises(ValueError):
            sq.create_query("biz-1", {"name": "x", "question": "?"})


def test_invalid_chart_type_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, sq, _ = _fresh(db)
        import pytest
        with pytest.raises(ValueError):
            sq.create_query("biz-1", {
                "name": "X", "question": "?", "chart_type": "doughnut",
            })


def test_record_run_bumps_count():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, sq, _ = _fresh(db)
        q = sq.create_query("biz-1", {"name": "X", "question": "?"})
        sq.record_run("biz-1", q["id"])
        sq.record_run("biz-1", q["id"])
        assert sq.get_query("biz-1", q["id"])["run_count"] == 2


def test_templates_exist():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, sq, _ = _fresh(db)
        tpls = sq.list_templates()
        keys = {t["key"] for t in tpls}
        assert "revenue_by_month" in keys
        assert "overdue_invoices" in keys
        assert len(tpls) >= 5


def test_create_from_template():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, sq, _ = _fresh(db)
        q = sq.create_from_template("biz-1", "top_customers")
        assert q["template_key"] == "top_customers"
        assert q["chart_type"] == "bar"


def test_unknown_template_raises():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, sq, _ = _fresh(db)
        import pytest
        with pytest.raises(ValueError):
            sq.create_from_template("biz-1", "missing")


# ── Structured research parser ─────────────────────────────────────────────
def test_research_parser_extracts_fields():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, _, ra = _fresh(db)
        sample = (
            "SUMMARY: Acme is a B2B SaaS company based in Bengaluru.\n"
            "FINDING: Employee count || ~150 engineers\n"
            "FINDING: Primary market || Mid-market CFOs in India\n"
            "SOURCE: Company website\n"
            "SOURCE: Latest funding announcement\n"
            "NEXT: Check if they're hiring our target profile\n"
            "NEXT: Look up their CTO on LinkedIn\n"
        )
        summary, findings, sources, next_steps = ra._parse_structured(sample)
        assert summary.startswith("Acme")
        assert len(findings) == 2
        assert findings[0]["title"] == "Employee count"
        assert findings[0]["detail"] == "~150 engineers"
        assert len(sources) == 2
        assert len(next_steps) == 2


def test_research_parser_tolerates_missing_fields():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, _, ra = _fresh(db)
        summary, findings, sources, next_steps = ra._parse_structured("SUMMARY: hi")
        assert summary == "hi"
        assert findings == []
        assert sources == []
        assert next_steps == []


def test_research_parser_handles_finding_without_delimiter():
    with tempfile.TemporaryDirectory() as tmp:
        db = os.path.join(tmp, "nexus.db")
        _, _, _, ra = _fresh(db)
        _, findings, _, _ = ra._parse_structured("FINDING: Just a title with no detail")
        assert len(findings) == 1
        assert findings[0]["title"].startswith("Just a title")
        assert findings[0]["detail"] == ""
