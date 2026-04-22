"""Tests for v2.0 new features: conversation persistence, query history, data import, export."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
import pytest

class TestConversationStore:
    def test_crud(self):
        from memory.conversation_store import create_conversation, save_message, load_messages, delete_conversation, get_conversation_info
        cid = create_conversation("Test")
        save_message(cid, "user", "Hello")
        save_message(cid, "assistant", "Hi!", tools_used=["rag"])
        msgs = load_messages(cid)
        assert len(msgs) == 2
        assert msgs[1]["tools_used"] == ["rag"]
        info = get_conversation_info(cid)
        assert info["message_count"] == 2
        delete_conversation(cid)
        assert get_conversation_info(cid) is None

    def test_full_save(self):
        from memory.conversation_store import create_conversation, save_full_conversation, load_messages, delete_conversation
        cid = create_conversation("Full")
        msgs = [{"role": "user", "content": "Q1"}, {"role": "assistant", "content": "A1", "tools_used": ["sql"]}]
        save_full_conversation(cid, msgs)
        loaded = load_messages(cid)
        assert len(loaded) == 2
        delete_conversation(cid)

    def test_list_and_title(self):
        from memory.conversation_store import create_conversation, list_conversations, auto_title, get_conversation_info, delete_conversation
        cid = create_conversation()
        auto_title(cid, "Show me revenue by region for last quarter")
        info = get_conversation_info(cid)
        assert len(info["title"]) <= 63
        convs = list_conversations()
        assert any(c["conversation_id"] == cid for c in convs)
        delete_conversation(cid)

class TestQueryHistory:
    def test_log_and_search(self):
        from memory.query_history import log_query, get_history
        log_query("unique_test_qh_xyz", intent="data_query", tools_used=["sql"], answer_preview="answer", duration_ms=100)
        results = get_history(search="unique_test_qh_xyz")
        assert len(results) >= 1

    def test_star(self):
        from memory.query_history import log_query, toggle_star
        qid = log_query("star test", intent="chitchat")
        assert toggle_star(qid) is True
        assert toggle_star(qid) is False

    def test_stats(self):
        from memory.query_history import get_stats
        stats = get_stats()
        assert "total_queries" in stats
        assert "top_intents" in stats

class TestDataImport:
    def test_sanitize(self):
        from sql_agent.data_import import _sanitize_table_name, _sanitize_column_name
        assert _sanitize_table_name("My Data.csv") == "my_data"
        assert _sanitize_column_name("Revenue ($)") == "revenue"

    def test_import_df(self):
        import pandas as pd, sqlite3
        from sql_agent.data_import import import_to_database, get_existing_tables
        from config.settings import DB_PATH
        df = pd.DataFrame({"name": ["A", "B"], "val": [1, 2]})
        res = import_to_database(df, "test_import_temp", if_exists="replace")
        assert res["success"]
        assert "test_import_temp" in get_existing_tables()
        conn = sqlite3.connect(DB_PATH); conn.execute("DROP TABLE IF EXISTS test_import_temp"); conn.commit(); conn.close()

    def test_protected(self):
        import pandas as pd
        from sql_agent.data_import import import_to_database
        res = import_to_database(pd.DataFrame({"x": [1]}), "customers", if_exists="replace")
        assert not res["success"]

class TestExport:
    def _msgs(self):
        return [{"role": "user", "content": "Hello", "tools_used": [], "timestamp": "10:00"},
                {"role": "assistant", "content": "Hi!", "tools_used": ["rag"], "timestamp": "10:01"}]

    def test_markdown(self):
        from utils.export_conversation import to_markdown
        md = to_markdown(self._msgs(), "Test")
        assert "# Test" in md and "Hello" in md and "rag" in md

    def test_pdf(self):
        from utils.export_conversation import to_pdf
        path = to_pdf(self._msgs(), "Test")
        assert Path(path).exists() and Path(path).stat().st_size > 0
        Path(path).unlink()

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
