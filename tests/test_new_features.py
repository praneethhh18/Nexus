"""
Tests for v2.0 new features: conversation persistence, query history,
data import, and conversation export.

Run: pytest tests/test_new_features.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
#   CONVERSATION STORE TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestConversationStore:
    """Tests for memory/conversation_store.py"""

    def test_create_and_delete(self):
        from memory.conversation_store import (
            create_conversation, delete_conversation, get_conversation_info,
        )
        cid = create_conversation("Test Conv")
        info = get_conversation_info(cid)
        assert info is not None
        assert info["title"] == "Test Conv"
        assert info["message_count"] == 0
        delete_conversation(cid)
        assert get_conversation_info(cid) is None

    def test_save_and_load_messages(self):
        from memory.conversation_store import (
            create_conversation, save_message, load_messages, delete_conversation,
        )
        cid = create_conversation("Msg Test")
        save_message(cid, "user", "Hello")
        save_message(cid, "assistant", "Hi!", tools_used=["rag"])
        msgs = load_messages(cid)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"
        assert msgs[0]["content"] == "Hello"
        assert msgs[1]["tools_used"] == ["rag"]
        delete_conversation(cid)

    def test_save_full_conversation(self):
        from memory.conversation_store import (
            create_conversation, save_full_conversation, load_messages,
            delete_conversation, get_conversation_info,
        )
        cid = create_conversation("Full Save Test")
        messages = [
            {"role": "user", "content": "Q1", "timestamp": "10:00"},
            {"role": "assistant", "content": "A1", "tools_used": ["sql"], "timestamp": "10:01"},
            {"role": "user", "content": "Q2", "timestamp": "10:02"},
        ]
        save_full_conversation(cid, messages)
        loaded = load_messages(cid)
        assert len(loaded) == 3
        info = get_conversation_info(cid)
        assert info["message_count"] == 3
        delete_conversation(cid)

    def test_list_conversations(self):
        from memory.conversation_store import (
            create_conversation, list_conversations, delete_conversation,
        )
        cid1 = create_conversation("List Test 1")
        cid2 = create_conversation("List Test 2")
        convs = list_conversations()
        ids = [c["conversation_id"] for c in convs]
        assert cid1 in ids
        assert cid2 in ids
        delete_conversation(cid1)
        delete_conversation(cid2)

    def test_auto_title(self):
        from memory.conversation_store import (
            create_conversation, auto_title, get_conversation_info, delete_conversation,
        )
        cid = create_conversation()
        auto_title(cid, "Show me revenue by region for the last quarter please")
        info = get_conversation_info(cid)
        assert len(info["title"]) <= 63  # 60 + "..."
        delete_conversation(cid)

    def test_update_title(self):
        from memory.conversation_store import (
            create_conversation, update_title, get_conversation_info, delete_conversation,
        )
        cid = create_conversation("Old Title")
        update_title(cid, "New Title")
        info = get_conversation_info(cid)
        assert info["title"] == "New Title"
        delete_conversation(cid)


# ═══════════════════════════════════════════════════════════════════════════════
#   QUERY HISTORY TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestQueryHistory:
    """Tests for memory/query_history.py"""

    def test_log_and_retrieve(self):
        from memory.query_history import log_query, get_history
        qid = log_query(
            "test query for history",
            intent="data_query",
            tools_used=["sql"],
            answer_preview="test answer",
            duration_ms=100,
        )
        assert qid > 0
        history = get_history(search="test query for history")
        assert len(history) >= 1
        assert any(h["query"] == "test query for history" for h in history)

    def test_search_filter(self):
        from memory.query_history import log_query, get_history
        log_query("unique_search_xyz_123", intent="document_query")
        results = get_history(search="unique_search_xyz_123")
        assert len(results) >= 1

    def test_intent_filter(self):
        from memory.query_history import log_query, get_history
        log_query("intent filter test", intent="whatif_query")
        results = get_history(intent_filter="whatif_query")
        assert len(results) >= 1

    def test_star_toggle(self):
        from memory.query_history import log_query, toggle_star, get_history
        qid = log_query("star test query", intent="chitchat")
        starred = toggle_star(qid)
        assert starred is True
        unstarred = toggle_star(qid)
        assert unstarred is False

    def test_stats(self):
        from memory.query_history import get_stats
        stats = get_stats()
        assert "total_queries" in stats
        assert "avg_duration_ms" in stats
        assert "success_rate_pct" in stats
        assert "top_intents" in stats

    def test_delete_query(self):
        from memory.query_history import log_query, delete_query, get_history
        qid = log_query("delete me query", intent="chitchat")
        delete_query(qid)
        results = get_history(search="delete me query")
        assert not any(h["id"] == qid for h in results)


# ═══════════════════════════════════════════════════════════════════════════════
#   DATA IMPORT TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestDataImport:
    """Tests for sql_agent/data_import.py"""

    def test_sanitize_table_name(self):
        from sql_agent.data_import import _sanitize_table_name
        assert _sanitize_table_name("My Data.csv") == "my_data"
        assert _sanitize_table_name("123_report.xlsx") == "report"
        assert _sanitize_table_name("Sales (Q3 2025).csv") == "sales_q3_2025"
        assert _sanitize_table_name("...") == "imported_data"

    def test_sanitize_column_name(self):
        from sql_agent.data_import import _sanitize_column_name
        assert _sanitize_column_name("Total Revenue ($)") == "total_revenue"
        assert _sanitize_column_name("Customer Name") == "customer_name"
        assert _sanitize_column_name("123count") == "count"

    def test_import_and_query_dataframe(self):
        import pandas as pd
        from sql_agent.data_import import import_to_database, get_existing_tables
        import sqlite3
        from config.settings import DB_PATH

        df = pd.DataFrame({
            "name": ["Alice", "Bob", "Charlie"],
            "score": [90, 85, 92],
        })
        result = import_to_database(df, "test_import_xyz", if_exists="replace")
        assert result["success"]
        assert result["rows_imported"] == 3
        assert "test_import_xyz" in get_existing_tables()

        # Clean up
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DROP TABLE IF EXISTS test_import_xyz")
        conn.commit()
        conn.close()

    def test_protected_table_rejection(self):
        import pandas as pd
        from sql_agent.data_import import import_to_database

        df = pd.DataFrame({"x": [1]})
        result = import_to_database(df, "customers", if_exists="replace")
        assert not result["success"]
        assert "protected" in result["error"].lower()

    def test_get_existing_tables(self):
        from sql_agent.data_import import get_existing_tables
        tables = get_existing_tables()
        assert isinstance(tables, list)
        assert len(tables) > 0  # At least the nexus system tables


# ═══════════════════════════════════════════════════════════════════════════════
#   CONVERSATION EXPORT TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestConversationExport:
    """Tests for utils/export_conversation.py"""

    def _sample_messages(self):
        return [
            {"role": "user", "content": "Hello", "tools_used": [], "timestamp": "10:00"},
            {
                "role": "assistant", "content": "Hi! How can I help?",
                "tools_used": ["rag"], "citations": [{"source": "doc.pdf", "page": 1, "confidence": 0.9}],
                "sources_used": ["doc.pdf"], "multi_agent": False, "agents_used": [],
                "timestamp": "10:01",
            },
        ]

    def test_to_markdown(self):
        from utils.export_conversation import to_markdown
        md = to_markdown(self._sample_messages(), "Test Export")
        assert "# Test Export" in md
        assert "Hello" in md
        assert "Hi! How can I help?" in md
        assert "Tools used:" in md
        assert "rag" in md
        assert "doc.pdf" in md

    def test_to_markdown_empty(self):
        from utils.export_conversation import to_markdown
        md = to_markdown([], "Empty")
        assert "# Empty" in md

    def test_save_markdown(self):
        from utils.export_conversation import save_markdown
        path = save_markdown(self._sample_messages(), "Save Test")
        assert Path(path).exists()
        content = Path(path).read_text(encoding="utf-8")
        assert "Hello" in content
        # Clean up
        Path(path).unlink()

    def test_to_pdf(self):
        from utils.export_conversation import to_pdf
        path = to_pdf(self._sample_messages(), "PDF Test")
        assert path
        assert Path(path).exists()
        assert Path(path).suffix == ".pdf"
        assert Path(path).stat().st_size > 0
        # Clean up
        Path(path).unlink()

    def test_to_pdf_empty(self):
        from utils.export_conversation import to_pdf
        path = to_pdf([], "Empty PDF")
        assert path
        assert Path(path).exists()
        Path(path).unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
