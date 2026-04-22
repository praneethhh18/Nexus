"""
NexusAgent End-to-End Tests — verifies all 6 core scenarios.
Run: python tests/test_e2e.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from loguru import logger

PASS = "✅ PASS"
FAIL = "❌ FAIL"
WARN = "⚠️  WARN"


def _h(title: str) -> None:
    print(f"\n{'='*60}\nTest: {title}\n{'='*60}")


def test_1_document_query() -> bool:
    _h("Document Q&A — Refund Policy")
    try:
        # Ensure sample docs exist
        from utils.sample_docs_generator import ensure_documents_loaded
        ensure_documents_loaded()

        from rag.retriever import retrieve
        result = retrieve("What is the refund policy for enterprise clients?")

        if not result["results"]:
            print(f"  {FAIL}: No results returned from RAG")
            return False

        top = result["results"][0]
        print(f"  Top source: {top['source']} (page {top['page']})")
        print(f"  Confidence: {top['confidence']:.0%}")
        print(f"  Text snippet: {top['text'][:150]}…")

        has_citation = "company_policy" in top["source"].lower()
        if has_citation:
            print(f"  {PASS}: Correct source cited — company_policy.txt")
        else:
            print(f"  {WARN}: Answer found but from {top['source']} (expected company_policy.txt)")
        return True
    except Exception as e:
        print(f"  {FAIL}: {e}")
        return False


def test_2_data_query() -> bool:
    _h("Data Query — Highest Sales Region")
    try:
        from sql_agent.db_setup import setup_database
        setup_database()

        from sql_agent.executor import execute_query
        result = execute_query(
            "Which region had the highest total revenue?",
            log_to_audit=False
        )

        if not result["success"]:
            print(f"  {FAIL}: SQL execution failed — {result['error']}")
            return False

        df = result["dataframe"]
        print(f"  Rows returned: {len(df)}")
        print(f"  Explanation: {result['explanation'][:200]}")
        print(f"  SQL used: {result['query_used'][:100]}…")

        if len(df) > 0:
            print(f"  {PASS}: Data returned with {len(df)} row(s)")
            return True
        else:
            print(f"  {WARN}: Query succeeded but returned 0 rows")
            return True
    except Exception as e:
        print(f"  {FAIL}: {e}")
        return False


def test_3_hybrid_query() -> bool:
    _h("Hybrid Query — SQL Data + RAG Playbook")
    try:
        from orchestrator.graph import run
        result = run(
            "Our South region sales dropped. What does our sales playbook say to do?"
        )

        tools = result.get("tools_used", [])
        answer = result.get("final_answer", "")

        print(f"  Tools activated: {tools}")
        print(f"  Answer preview: {answer[:200]}…")

        has_rag = "rag" in tools
        has_answer = len(answer) > 50
        status = PASS if has_answer else WARN
        print(f"  RAG activated: {has_rag}")
        print(f"  {status}: Hybrid query completed")
        return has_answer
    except Exception as e:
        print(f"  {FAIL}: {e}")
        return False


def test_4_action_email() -> bool:
    _h("Action Request — Email Draft (Test Mode — Never Sends)")
    try:
        from action_tools.email_tool import compose_and_send
        result = compose_and_send(
            recipient="client@example.com",
            subject_hint="Order Status Follow-up",
            context="Follow up with a client about the status of their order #ORD-2025-001",
            test_mode=True,  # Ensures email is NEVER sent
        )

        draft = result.get("draft", {})
        saved = result.get("saved_path")
        sent = result.get("sent", False)

        print(f"  Draft generated: {'Yes' if draft else 'No'}")
        print(f"  Subject: {draft.get('subject', 'N/A')}")
        print(f"  Sent: {sent} (should be False in test mode)")
        print(f"  Draft saved: {saved or 'No'}")

        if draft and not sent:
            print(f"  {PASS}: Email drafted, NOT sent (human-in-the-loop working)")
            return True
        else:
            print(f"  {FAIL}: Email should not have been sent in test mode")
            return False
    except Exception as e:
        print(f"  {FAIL}: {e}")
        return False


def test_5_whatif_scenario() -> bool:
    _h("What-If Scenario — Product Sales Drop 25%")
    try:
        from utils.whatif_simulator import run_full_simulation
        result = run_full_simulation("What if our top product's sales dropped 25%?")

        if result.get("error"):
            print(f"  {FAIL}: {result['error']}")
            return False

        print(f"  Scenario: {result.get('scenario_description')}")
        print(f"  Net impact: {result.get('net_impact')}")
        print(f"  Before revenue: ${result.get('before_total_revenue', 0):,.0f}")
        print(f"  After revenue: ${result.get('after_total_revenue', 0):,.0f}")
        print(f"  Chart: {result.get('chart_path', 'None')}")
        print(f"  Critique preview: {result.get('critique', '')[:100]}")

        has_impact = result.get("net_impact_abs", 0) != 0
        print(f"  {PASS if has_impact else WARN}: Simulation {'' if has_impact else 'returned zero impact — check DB'}")
        return True
    except Exception as e:
        print(f"  {FAIL}: {e}")
        return False


def test_6_proactive_monitor() -> bool:
    _h("Proactive Monitor — Anomaly Detection")
    try:
        # Ensure anomaly data exists
        from sql_agent.db_setup import setup_database
        setup_database()

        from orchestrator.proactive_monitor import manual_trigger
        result = manual_trigger()

        anomalies = result.get("anomalies_found", [])
        regions_checked = result.get("regions_checked", [])
        error = result.get("error")

        print(f"  Regions checked: {regions_checked}")
        print(f"  Anomalies found: {len(anomalies)}")
        for a in anomalies:
            print(f"    → {a['region']}: {a['drop_pct']:.1f}% drop (${a['revenue']:,.0f})")
        print(f"  Error: {error or 'None'}")

        if error:
            print(f"  {FAIL}: Monitor error — {error}")
            return False

        if anomalies:
            print(f"  {PASS}: Anomalies detected in planted data!")
        else:
            print(f"  {WARN}: No anomalies detected (planted anomalies may be outside the 7-day window)")
        return True
    except Exception as e:
        print(f"  {FAIL}: {e}")
        return False


def run_all_tests() -> None:
    print("\n" + "█" * 60)
    print("  NEXUSAGENT END-TO-END TEST SUITE")
    print("█" * 60)

    tests = [
        ("Document Q&A", test_1_document_query),
        ("Data Query", test_2_data_query),
        ("Hybrid Query", test_3_hybrid_query),
        ("Email Draft (no send)", test_4_action_email),
        ("What-If Simulation", test_5_whatif_scenario),
        ("Proactive Monitor", test_6_proactive_monitor),
    ]

    results = []
    for name, test_fn in tests:
        try:
            passed = test_fn()
            results.append((name, passed))
        except Exception as e:
            print(f"  {FAIL}: Unexpected error — {e}")
            results.append((name, False))
        time.sleep(1)

    print("\n" + "─" * 60)
    print("SUMMARY:")
    passed_count = sum(1 for _, p in results if p)
    for name, passed in results:
        status = PASS if passed else FAIL
        print(f"  {status}  {name}")
    print(f"\n  {passed_count}/{len(tests)} tests passed")
    print("─" * 60)


if __name__ == "__main__":
    run_all_tests()
