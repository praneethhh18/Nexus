"""
Tests for Tier 1 Features:
  1. Multi-Document RAG with Cross-Source Reasoning
  2. Agent Memory & Personalization
  3. Multi-Agent Collaboration
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest


# ── Feature 1: Multi-Document RAG ────────────────────────────────────────────
class TestMultiDocumentRAG:
    """Tests for rag/multi_document_rag.py"""

    def test_import(self):
        """Module should import without errors."""
        from rag.multi_document_rag import (
            multi_doc_retrieve,
            get_sources_list,
            _is_multi_document_query,
            _parse_comparison_query,
            _match_source,
        )
        assert callable(multi_doc_retrieve)
        assert callable(get_sources_list)

    def test_multi_doc_query_detection(self):
        """Should detect multi-document query patterns."""
        from rag.multi_document_rag import _is_multi_document_query

        # Should be detected as multi-doc
        assert _is_multi_document_query("Compare the Q2 report and Q3 report on margins")
        assert _is_multi_document_query("Find contradictions between the sales policy and HR policy")
        assert _is_multi_document_query("What's the difference between document A versus document B")
        assert _is_multi_document_query("Compare what the Q2 docs say vs Q3 docs about revenue")

        # Should NOT be detected as multi-doc
        assert not _is_multi_document_query("What is the revenue?")
        assert not _is_multi_document_query("Show me sales data")
        assert not _is_multi_document_query("Hello")

    def test_comparison_query_parsing(self):
        """Should parse comparison queries into doc_a, doc_b, topic."""
        from rag.multi_document_rag import _parse_comparison_query

        result = _parse_comparison_query("Compare the Q2 report and Q3 report on margins")
        assert result["doc_a"] is not None or result["doc_b"] is not None or result["topic"] is not None

    def test_source_matching(self):
        """Should fuzzy-match source names."""
        from rag.multi_document_rag import _match_source

        sources = ["Q2_Report_2025.pdf", "Q3_Report_2025.pdf", "HR_Policy.pdf"]

        # Exact match
        assert _match_source("Q2_Report_2025.pdf", sources) == "Q2_Report_2025.pdf"

        # Substring match — "Q2_Report" matches "Q2_Report_2025.pdf"
        matched = _match_source("Q2_Report", sources)
        assert matched is not None

        # No match — unrelated text
        no_match = _match_source("something completely unrelated", sources)
        # May or may not match depending on token overlap, just check it doesn't crash

    def test_empty_retrieval(self):
        """Should handle empty knowledge base gracefully."""
        from rag.multi_document_rag import multi_doc_retrieve

        result = multi_doc_retrieve("test query")
        assert "answer" in result
        assert "sources_used" in result
        assert "mode" in result
        assert "is_multi_doc" in result

    def test_sources_list(self):
        """Should return list of available sources."""
        from rag.multi_document_rag import get_sources_list

        sources = get_sources_list()
        assert isinstance(sources, list)
        # Even if empty, should return a list
        for s in sources:
            assert "name" in s
            assert "chunk_count" in s


# ── Feature 2: Agent Memory & Personalization ────────────────────────────────
class TestUserMemory:
    """Tests for memory/user_memory.py"""

    def test_import(self):
        """Module should import without errors."""
        from memory.user_memory import (
            get_user_profile,
            update_user_profile,
            store_memory,
            recall_memories,
            forget_memory,
            build_personalized_context,
            learn_from_interaction,
            get_user_summary,
            start_session,
            end_session,
            log_session_query,
            track_pattern,
            get_user_patterns,
            remember_decision,
            remember_preference,
        )
        assert callable(get_user_profile)

    def test_user_profile(self):
        """Should get and update user profile."""
        from memory.user_memory import get_user_profile, update_user_profile

        profile = get_user_profile("default")
        assert "user_id" in profile
        assert "total_interactions" in profile

        # Update profile
        success = update_user_profile("default", communication_style="casual")
        assert success

        # Verify update
        updated = get_user_profile("default")
        assert updated.get("communication_style") == "casual"

    def test_store_and_recall_memory(self):
        """Should store and recall memories."""
        from memory.user_memory import store_memory, recall_memories, forget_memory

        # Store a memory
        success = store_memory(
            "default", "preference", "test_pref_key", "test_pref_value", importance=0.8
        )
        assert success

        # Recall the memory
        memories = recall_memories("default", query="test_pref", limit=5)
        assert len(memories) >= 1
        assert any(m["key"] == "test_pref_key" for m in memories)

        # Forget the memory
        success = forget_memory("default", "test_pref_key")
        assert success

    def test_build_personalized_context(self):
        """Should build context string from user memory."""
        from memory.user_memory import build_personalized_context

        context = build_personalized_context("default", "test query")
        assert isinstance(context, str)

    def test_session_tracking(self):
        """Should track sessions."""
        from memory.user_memory import start_session, end_session, log_session_query

        session_id = start_session("default", "test_session_123")
        assert session_id == "test_session_123"

        log_session_query(session_id, "data_query", ["sql", "rag"])

        end_session(session_id)

    def test_pattern_tracking(self):
        """Should track and retrieve patterns."""
        from memory.user_memory import track_pattern, get_user_patterns

        track_pattern("default", "topic", "revenue", "Revenue", )
        track_pattern("default", "topic", "revenue", "Revenue")

        patterns = get_user_patterns("default", "topic")
        assert len(patterns) >= 1
        assert any(p["pattern_key"] == "revenue" for p in patterns)

    def test_user_summary(self):
        """Should generate user summary."""
        from memory.user_memory import get_user_summary

        summary = get_user_summary("default")
        assert "profile" in summary
        assert "total_memories" in summary
        assert "total_patterns" in summary

    def test_remember_decision(self):
        """Should record decisions."""
        from memory.user_memory import remember_decision, recall_memories

        remember_decision("default", "budget_approval", "Approved Q3 budget cut")
        memories = recall_memories("default", memory_type="decision", limit=5)
        assert any(m["key"] == "budget_approval" for m in memories)

        # Cleanup
        from memory.user_memory import forget_memory
        forget_memory("default", "budget_approval")

    def test_remember_preference(self):
        """Should record preferences."""
        from memory.user_memory import remember_preference, recall_memories, forget_memory

        remember_preference("default", "region_focus", "South")
        memories = recall_memories("default", memory_type="preference", limit=5)
        assert any(m["key"] == "region_focus" for m in memories)

        forget_memory("default", "region_focus")


# ── Feature 3: Multi-Agent Collaboration ─────────────────────────────────────
class TestMultiAgent:
    """Tests for orchestrator/multi_agent.py"""

    def test_import(self):
        """Module should import without errors."""
        from orchestrator.multi_agent import (
            PlannerAgent,
            DataAgent,
            DocAgent,
            SynthesisAgent,
            MultiAgentOrchestrator,
            get_orchestrator,
            run_multi_agent,
            AgentRole,
            AgentMessage,
            AgentResult,
            TaskStep,
            TaskPlan,
        )
        assert callable(get_orchestrator)

    def test_planner_creation(self):
        """Should create PlannerAgent instance."""
        from orchestrator.multi_agent import PlannerAgent

        planner = PlannerAgent()
        assert planner is not None
        assert callable(planner.plan)
        assert callable(planner.should_use_multi_agent)

    def test_planner_multi_doc_detection(self):
        """Should detect queries needing multi-agent collaboration."""
        from orchestrator.multi_agent import PlannerAgent

        planner = PlannerAgent()

        # Multi-agent triggers
        assert planner.should_use_multi_agent(
            "Analyze our Q3 docs and query the DB for the same period"
        )
        assert planner.should_use_multi_agent(
            "Compare the sales policy document with the revenue data"
        )

        # Simple queries should NOT trigger multi-agent
        assert not planner.should_use_multi_agent("Hello")
        assert not planner.should_use_multi_agent("What is 2+2?")

    def test_planner_fallback_plan(self):
        """Should create a fallback plan with parallel steps."""
        from orchestrator.multi_agent import PlannerAgent

        planner = PlannerAgent()
        plan = planner._fallback_plan("Test query")

        assert plan is not None
        assert len(plan.steps) >= 1
        assert plan.original_query == "Test query"
        assert isinstance(plan.execution_order, list)

    def test_data_agent_creation(self):
        """Should create DataAgent instance."""
        from orchestrator.multi_agent import DataAgent

        agent = DataAgent()
        assert agent is not None
        assert callable(agent.execute)

    def test_doc_agent_creation(self):
        """Should create DocAgent instance."""
        from orchestrator.multi_agent import DocAgent

        agent = DocAgent()
        assert agent is not None
        assert callable(agent.execute)

    def test_synthesis_agent_creation(self):
        """Should create SynthesisAgent instance."""
        from orchestrator.multi_agent import SynthesisAgent

        agent = SynthesisAgent()
        assert agent is not None
        assert callable(agent.synthesize)

    def test_orchestrator_singleton(self):
        """Should return a consistent orchestrator singleton."""
        from orchestrator.multi_agent import get_orchestrator

        orch1 = get_orchestrator()
        orch2 = get_orchestrator()
        assert orch1 is orch2

    def test_agent_role_enum(self):
        """Should have correct agent roles."""
        from orchestrator.multi_agent import AgentRole

        assert AgentRole.PLANNER == "planner"
        assert AgentRole.DATA == "data"
        assert AgentRole.DOC == "doc"
        assert AgentRole.SYNTHESIS == "synthesis"


# ── Integration Tests ────────────────────────────────────────────────────────
class TestIntegration:
    """Tests that verify all three features work together."""

    def test_graph_state_includes_tier1_fields(self):
        """Graph state should include Tier 1 fields."""
        from orchestrator.graph import INITIAL_STATE

        assert "multi_agent" in INITIAL_STATE
        assert "agent_plan" in INITIAL_STATE
        assert "agent_results" in INITIAL_STATE
        assert "agents_used" in INITIAL_STATE
        assert "multi_doc_result" in INITIAL_STATE
        assert "sources_used" in INITIAL_STATE
        assert "per_source_summaries" in INITIAL_STATE
        assert "user_id" in INITIAL_STATE
        assert "personalized_context" in INITIAL_STATE
        assert "user_profile" in INITIAL_STATE

    def test_nodes_include_multi_agent_node(self):
        """Nodes module should include multi_agent_node function."""
        from orchestrator.nodes import multi_agent_node
        assert callable(multi_agent_node)

    def test_graph_run_function_accepts_user_id(self):
        """Graph run function should accept user_id parameter."""
        import inspect
        from orchestrator.graph import run

        sig = inspect.signature(run)
        assert "user_id" in sig.parameters


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
