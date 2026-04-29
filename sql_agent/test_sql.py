"""
SQL Agent Test Script — creates DB and runs 5 NL queries.
Run: python sql_agent/test_sql.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))


QUESTIONS = [
    "Which region had the highest total revenue?",
    "What are the top 5 products by total order value?",
    "How many customers are in each segment?",
    "What is the average order amount by status?",
    "Show me the sales trend by month for the last 6 months",
]


def main():
    from config.settings import ensure_directories
    ensure_directories()

    from sql_agent.db_setup import setup_database
    setup_database()

    from sql_agent.executor import execute_query

    print("\n" + "="*60)
    print("SQL AGENT TEST — 5 NATURAL LANGUAGE QUERIES")
    print("="*60)

    passed = 0
    for i, question in enumerate(QUESTIONS, 1):
        print(f"\nTest {i}: {question}")
        result = execute_query(question, log_to_audit=False)

        if result["success"]:
            df = result["dataframe"]
            print(f"  SQL used: {result['query_used'][:100]}...")
            print(f"  Rows returned: {len(df)}")
            print(f"  Retries needed: {result['retries_needed']}")
            print(f"  Explanation: {result['explanation'][:200]}")
            print("  PASS")
            passed += 1
        else:
            print(f"  Error: {result['error']}")
            print("  FAIL")

    print("\n" + "="*60)
    print(f"SQL TESTS: {passed}/{len(QUESTIONS)} passed")
    print("="*60)


if __name__ == "__main__":
    main()
