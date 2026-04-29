"""
NexusAgent Core Unit Tests — pytest-based test suite.
Tests configuration, SQL generation/validation, RAG detection, intent parsing,
and module structure without requiring Ollama to be running.

Run: pytest tests/test_core.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest


# ═══════════════════════════════════════════════════════════════════════════════
#   CONFIGURATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestConfig:
    """Tests for config/settings.py — validates all settings load correctly."""

    def test_settings_import(self):
        from config.settings import (
            OLLAMA_BASE_URL, OLLAMA_MODEL, EMBED_MODEL,
            DB_PATH, CHROMA_PATH, OUTPUTS_DIR, REPORTS_DIR,
            MAX_SQL_RETRIES, CHUNK_SIZE, CHUNK_OVERLAP, VERSION,
        )
        assert OLLAMA_BASE_URL
        assert OLLAMA_MODEL
        assert EMBED_MODEL
        assert DB_PATH
        assert VERSION

    def test_directories_exist_after_ensure(self):
        from config.settings import (
            ensure_directories, OUTPUTS_DIR, REPORTS_DIR,
            EMAIL_DRAFTS_DIR, DOCUMENTS_DIR, CHROMA_PATH,
        )
        ensure_directories()
        assert Path(OUTPUTS_DIR).is_dir()
        assert Path(REPORTS_DIR).is_dir()
        assert Path(EMAIL_DRAFTS_DIR).is_dir()
        assert Path(DOCUMENTS_DIR).is_dir()
        assert Path(CHROMA_PATH).is_dir()

    def test_validate_config_returns_dict(self):
        from config.settings import validate_config
        result = validate_config()
        assert isinstance(result, dict)
        assert "valid" in result
        assert "issues" in result
        assert "warnings" in result
        assert "version" in result

    def test_chunk_overlap_less_than_size(self):
        from config.settings import CHUNK_SIZE, CHUNK_OVERLAP
        assert CHUNK_OVERLAP < CHUNK_SIZE, (
            f"CHUNK_OVERLAP ({CHUNK_OVERLAP}) must be less than CHUNK_SIZE ({CHUNK_SIZE})"
        )

    def test_numeric_settings_in_range(self):
        from config.settings import MAX_SQL_RETRIES, MAX_REFLECTION_RETRIES, TOP_K_RETRIEVAL
        assert 0 <= MAX_SQL_RETRIES <= 10
        assert 0 <= MAX_REFLECTION_RETRIES <= 5
        assert 1 <= TOP_K_RETRIEVAL <= 50


# ═══════════════════════════════════════════════════════════════════════════════
#   SQL AGENT TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestSQLValidation:
    """Tests for sql_agent/query_generator.py — SQL validation and extraction."""

    def test_validate_select(self):
        from sql_agent.query_generator import _validate_sql
        assert _validate_sql("SELECT * FROM customers")
        assert _validate_sql("SELECT name, revenue FROM sales_metrics WHERE region='North'")
        assert _validate_sql("WITH cte AS (SELECT * FROM orders) SELECT * FROM cte")

    def test_block_destructive_sql(self):
        from sql_agent.query_generator import _validate_sql
        assert not _validate_sql("DROP TABLE customers")
        assert not _validate_sql("DELETE FROM customers")
        assert not _validate_sql("INSERT INTO customers VALUES (1, 'test')")
        assert not _validate_sql("UPDATE customers SET name='test'")
        assert not _validate_sql("TRUNCATE TABLE orders")
        assert not _validate_sql("ALTER TABLE customers ADD COLUMN x")
        assert not _validate_sql("CREATE TABLE hack (id INT)")

    def test_block_system_commands(self):
        from sql_agent.query_generator import _validate_sql
        assert not _validate_sql("ATTACH DATABASE '/etc/passwd' AS x")
        assert not _validate_sql("PRAGMA table_info(customers)")

    def test_reject_empty(self):
        from sql_agent.query_generator import _validate_sql
        assert not _validate_sql("")
        assert not _validate_sql("   ")
        assert not _validate_sql(None)

    def test_reject_non_select(self):
        from sql_agent.query_generator import _validate_sql
        assert not _validate_sql("Hello world")
        assert not _validate_sql("This is not SQL")

    def test_extract_sql_from_markdown(self):
        from sql_agent.query_generator import _extract_sql
        raw = "Here is the query:\n```sql\nSELECT * FROM customers;\n```\nDone."
        assert _extract_sql(raw) == "SELECT * FROM customers;"

    def test_extract_sql_without_fences(self):
        from sql_agent.query_generator import _extract_sql
        raw = "SELECT name, revenue FROM sales_metrics ORDER BY revenue DESC LIMIT 10;"
        result = _extract_sql(raw)
        assert "SELECT" in result
        assert "FROM" in result

    def test_extract_sql_from_prose(self):
        from sql_agent.query_generator import _extract_sql
        raw = "The answer is:\nSQL: SELECT COUNT(*) FROM orders;"
        result = _extract_sql(raw)
        assert "SELECT" in result

    def test_intent_detection(self):
        from sql_agent.query_generator import _detect_intent
        assert _detect_intent("Show revenue trend over time", "SELECT month, SUM(revenue) FROM sales GROUP BY month") == "trend"
        assert _detect_intent("Compare North vs South", "SELECT region, SUM(revenue) FROM sales GROUP BY region") == "comparison"
        assert _detect_intent("What is total revenue?", "SELECT SUM(revenue) FROM sales_metrics") == "aggregation"
        assert _detect_intent("Find the top customer", "SELECT name FROM customers ORDER BY revenue DESC LIMIT 1") == "lookup"

    def test_cache_operations(self):
        from sql_agent.query_generator import _query_cache, clear_cache, _normalize_question
        clear_cache()
        assert len(_query_cache) == 0

        key = _normalize_question("Test Question")
        assert key == "test question"


# ═══════════════════════════════════════════════════════════════════════════════
#   RAG DETECTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestRAGDetection:
    """Tests for rag/multi_document_rag.py — query classification and source matching."""

    def test_multi_doc_detection_positive(self):
        from rag.multi_document_rag import _is_multi_document_query
        assert _is_multi_document_query("Compare the Q2 report and Q3 report")
        assert _is_multi_document_query("Find contradictions between policy A and policy B")
        assert _is_multi_document_query("What's the difference between the two documents?")
        assert _is_multi_document_query("What do both reports say about revenue?")

    def test_multi_doc_detection_negative(self):
        from rag.multi_document_rag import _is_multi_document_query
        assert not _is_multi_document_query("What is the revenue?")
        assert not _is_multi_document_query("Hello there")
        assert not _is_multi_document_query("Show me sales data for Q3")

    def test_comparison_parsing(self):
        from rag.multi_document_rag import _parse_comparison_query
        result = _parse_comparison_query("Compare the Q2 report and Q3 report on margins")
        assert isinstance(result, dict)
        assert "doc_a" in result
        assert "doc_b" in result
        assert "topic" in result

    def test_source_matching_exact(self):
        from rag.multi_document_rag import _match_source
        sources = ["report_q2_2025.pdf", "report_q3_2025.pdf", "company_policy.txt"]
        assert _match_source("report_q2_2025.pdf", sources) == "report_q2_2025.pdf"

    def test_source_matching_substring(self):
        from rag.multi_document_rag import _match_source
        sources = ["report_q2_2025.pdf", "report_q3_2025.pdf"]
        result = _match_source("q2", sources)
        assert result == "report_q2_2025.pdf"

    def test_source_matching_no_match(self):
        from rag.multi_document_rag import _match_source
        sources = ["report.pdf"]
        result = _match_source("completely unrelated xyz", sources)
        # Should return None since Jaccard similarity < 0.2
        assert result is None

    def test_source_matching_empty(self):
        from rag.multi_document_rag import _match_source
        assert _match_source("", []) is None
        assert _match_source(None, []) is None
        assert _match_source("test", []) is None

    def test_deduplication(self):
        from rag.multi_document_rag import _deduplicate_chunks
        chunks = [
            {"text": "Revenue increased in Q3 by 15% across all regions"},
            {"text": "Revenue increased in Q3 by 15% across all regions"},  # exact dup
            {"text": "The South region showed strong growth in customer acquisition"},
        ]
        result = _deduplicate_chunks(chunks)
        assert len(result) == 2  # one duplicate removed

    def test_deduplication_empty(self):
        from rag.multi_document_rag import _deduplicate_chunks
        assert _deduplicate_chunks([]) == []

    def test_confidence_conversion(self):
        from rag.multi_document_rag import _distance_to_confidence
        assert _distance_to_confidence(0.0) == 1.0
        assert _distance_to_confidence(2.0) == 0.0
        assert 0 < _distance_to_confidence(0.5) < 1.0


# ═══════════════════════════════════════════════════════════════════════════════
#   INTENT DETECTOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestIntentDetector:
    """Tests for orchestrator/intent_detector.py — configuration and mappings."""

    def test_intent_types_defined(self):
        from orchestrator.intent_detector import INTENT_TYPES
        assert "document_query" in INTENT_TYPES
        assert "data_query" in INTENT_TYPES
        assert "hybrid_query" in INTENT_TYPES
        assert "action_request" in INTENT_TYPES
        assert "report_request" in INTENT_TYPES
        assert "whatif_query" in INTENT_TYPES
        assert "chitchat" in INTENT_TYPES

    def test_tool_map_covers_all_intents(self):
        from orchestrator.intent_detector import INTENT_TYPES, TOOL_MAP
        for intent in INTENT_TYPES:
            assert intent in TOOL_MAP, f"Missing TOOL_MAP entry for intent: {intent}"

    def test_urgency_keywords(self):
        from orchestrator.intent_detector import URGENCY_KEYWORDS
        assert "urgent" in URGENCY_KEYWORDS
        assert "asap" in URGENCY_KEYWORDS
        assert "critical" in URGENCY_KEYWORDS

    def test_detect_intent_empty_query(self):
        from orchestrator.intent_detector import detect_intent
        result = detect_intent("", {}, "")
        assert result["primary_intent"] == "chitchat"
        assert result["tools_needed"] == []


# ═══════════════════════════════════════════════════════════════════════════════
#   GRAPH / ORCHESTRATOR TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestOrchestrator:
    """Tests for orchestrator/graph.py — routing logic and state management."""

    def test_initial_state_completeness(self):
        from orchestrator.graph import INITIAL_STATE
        required_keys = [
            "query", "tone", "intent", "rag_results", "sql_results",
            "final_answer", "citations", "tools_used", "multi_agent",
            "user_id", "sources_used",
        ]
        for key in required_keys:
            assert key in INITIAL_STATE, f"Missing key in INITIAL_STATE: {key}"

    def test_route_intent_chitchat(self):
        from orchestrator.graph import _route_intent
        state = {
            "intent": {"primary_intent": "chitchat", "tools_needed": []},
            "multi_agent": False,
        }
        assert _route_intent(state) == "chitchat"

    def test_route_intent_rag(self):
        from orchestrator.graph import _route_intent
        state = {
            "intent": {"primary_intent": "document_query", "tools_needed": ["rag"]},
            "multi_agent": False,
        }
        assert _route_intent(state) == "rag"

    def test_route_intent_sql(self):
        from orchestrator.graph import _route_intent
        state = {
            "intent": {"primary_intent": "data_query", "tools_needed": ["sql"]},
            "multi_agent": False,
        }
        assert _route_intent(state) == "sql"

    def test_route_intent_multi_agent(self):
        from orchestrator.graph import _route_intent
        state = {
            "intent": {"primary_intent": "hybrid_query", "tools_needed": ["rag", "sql"]},
            "multi_agent": True,
        }
        assert _route_intent(state) == "multi_agent"

    def test_route_after_rag(self):
        from orchestrator.graph import _route_after_rag
        state = {
            "intent": {"primary_intent": "hybrid_query", "tools_needed": ["rag", "sql"]},
        }
        assert _route_after_rag(state) == "sql"

    def test_route_after_sql_to_report(self):
        from orchestrator.graph import _route_after_sql
        state = {
            "intent": {"primary_intent": "report_request", "tools_needed": ["sql", "report"]},
        }
        assert _route_after_sql(state) == "report"

    def test_reflection_max_retries(self):
        from orchestrator.graph import _route_reflection
        try:
            from langgraph.graph import END
        except ImportError:
            END = "__end__"
        state = {"reflection_passed": False, "reflection_attempts": 5}
        assert _route_reflection(state) == END

    def test_run_function_signature(self):
        import inspect
        from orchestrator.graph import run
        sig = inspect.signature(run)
        assert "query" in sig.parameters
        assert "user_id" in sig.parameters
        assert "tone" in sig.parameters


# ═══════════════════════════════════════════════════════════════════════════════
#   VOICE MODULE TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestVoice:
    """Tests for voice/ modules — import checks and configuration."""

    def test_tone_analyzer_tones(self):
        from voice.tone_analyzer import TONES, RESPONSE_STYLES
        assert len(TONES) >= 5
        for tone in TONES:
            assert tone in RESPONSE_STYLES, f"Missing RESPONSE_STYLES for tone: {tone}"

    def test_speaker_truncation(self):
        from voice.speaker import _truncate_for_speech
        long_text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
        result = _truncate_for_speech(long_text, max_sentences=2)
        # Should have at most 2 sentences
        assert result.count(". ") <= 2

    def test_listener_is_available_callable(self):
        from voice.listener import is_available
        # Should return bool without crashing
        result = is_available()
        assert isinstance(result, bool)


# ═══════════════════════════════════════════════════════════════════════════════
#   ACTION TOOLS TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestActionTools:
    """Tests for action_tools/ — configuration and validation."""

    def test_discord_severity_colors(self):
        from action_tools.discord_tool import SEVERITY_COLORS
        assert "info" in SEVERITY_COLORS
        assert "warning" in SEVERITY_COLORS
        assert "critical" in SEVERITY_COLORS
        assert "success" in SEVERITY_COLORS

    def test_discord_webhook_validation(self):
        from action_tools.discord_tool import _validate_webhook_url
        assert _validate_webhook_url("https://discord.com/api/webhooks/123/abc")
        assert _validate_webhook_url("https://discordapp.com/api/webhooks/123/abc")
        assert not _validate_webhook_url("https://example.com/webhook")
        assert not _validate_webhook_url("")
        assert not _validate_webhook_url("not-a-url")

    def test_file_dispatcher_import(self):
        from action_tools.file_dispatcher import get_recent_outputs
        result = get_recent_outputs(n=5, subfolder="reports")
        assert isinstance(result, list)


# ═══════════════════════════════════════════════════════════════════════════════
#   SELF-REFLECTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════
class TestSelfReflection:
    """Tests for orchestrator/self_reflection.py — edge cases."""

    def test_max_retries_auto_pass(self):
        from orchestrator.self_reflection import reflect
        result = reflect("test", "test answer", attempt=10)
        assert result["passed"] is True

    def test_empty_answer_fails(self):
        from orchestrator.self_reflection import reflect
        result = reflect("What is revenue?", "", attempt=0)
        assert result["passed"] is False

    def test_short_answer_fails(self):
        from orchestrator.self_reflection import reflect
        result = reflect("Complex question?", "Yes.", attempt=0)
        assert result["passed"] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
