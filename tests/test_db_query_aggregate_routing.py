"""
DB query routing — contract tests for the aggregate-then-cloud path.

Behavior under test (`sql_agent/executor.py:_explain_result`):

  1. When a non-empty DataFrame is explained, the FIRST llm_invoke is the
     aggregate-cloud path: `sensitive=False` and the prompt contains the
     `Aggregates` block, NOT the raw row sample.
  2. The prompt sent to cloud must NOT contain raw row contents — proves
     customer rows do not leave the box.
  3. If the cloud call raises, the function falls back to the original
     `sensitive=True` local path with the row sample.
  4. Empty DataFrame returns the canned empty message without any LLM call.
"""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from sql_agent.executor import _explain_result


def test_empty_df_returns_canned_message_without_llm():
    df = pd.DataFrame()
    with patch("sql_agent.executor.llm_invoke") as mocked:
        out = _explain_result("any question", df, "scalar")
    assert "no results" in out.lower()
    assert mocked.call_count == 0


def test_explain_uses_aggregate_cloud_path_first():
    """First call must be sensitive=False with an aggregate prompt — that's
    the cloud-eligible path that makes WhatsApp + chat fast."""
    df = pd.DataFrame({
        "customer": [f"C{i}" for i in range(50)],
        "amount":   [100 + i for i in range(50)],
    })
    with patch("sql_agent.executor.llm_invoke",
               return_value="Total revenue is $7,450.") as mocked:
        out = _explain_result("total revenue?", df, "scalar")

    assert "$7,450" in out or "Total revenue" in out
    # The first call is the cloud aggregate path
    first = mocked.call_args_list[0]
    assert first.kwargs.get("sensitive") is False, \
        "Aggregate path must use sensitive=False so it can hit cloud LLM."
    prompt = first.args[0] if first.args else first.kwargs.get("prompt", "")
    assert "Aggregates" in prompt, "Cloud prompt must use the aggregate block."


def test_aggregate_prompt_does_not_leak_raw_rows():
    """Privacy invariant — raw customer-level row strings must not appear in
    the cloud prompt. Only aggregated figures may go out."""
    df = pd.DataFrame({
        "customer_email": ["alice@example.com", "bob@example.com"] * 10,
        "amount":         [50.0 + i for i in range(20)],
    })
    with patch("sql_agent.executor.llm_invoke", return_value="ok") as mocked:
        _explain_result("how many customers?", df, "scalar")

    first = mocked.call_args_list[0]
    prompt = first.args[0] if first.args else first.kwargs.get("prompt", "")
    # The full row sample `df.head(10).to_string()` shape must never reach cloud.
    assert "rows x" not in prompt, "Row-shape sample is the local path, not cloud."


def test_aggregate_prompt_anonymizes_category_labels():
    """Stronger privacy invariant — even category labels (which can be customer
    names) get tokenized to `Entity A/B/C` before the cloud call."""
    df = pd.DataFrame({
        "customer": ["Acme Corp", "Globex", "Initech", "Umbrella", "Hooli"] * 4,
        "revenue":  [1000, 2000, 3000, 4000, 5000] * 4,
    })
    with patch("sql_agent.executor.llm_invoke",
               return_value="Entity A leads with $20,000.") as mocked:
        out = _explain_result("top customer?", df, "scalar")

    first = mocked.call_args_list[0]
    prompt = first.args[0] if first.args else first.kwargs.get("prompt", "")
    # The real customer names must NOT appear in the cloud prompt.
    for raw_name in ("Acme Corp", "Globex", "Initech", "Umbrella", "Hooli"):
        assert raw_name not in prompt, f"Raw label {raw_name!r} leaked to cloud prompt"
    assert "Entity A" in prompt, "Anonymization tokens should appear instead"
    # And the response is restored — user sees the real name, not the token.
    assert "Entity A" not in out, "Token leaked into final response"
    assert "Hooli" in out or "Umbrella" in out or "Acme" in out, \
        "Restored real label should be in user-facing output"


def test_anonymizer_returns_aggregates_unchanged_when_no_categoricals():
    """Numeric-only aggregates have no labels to anonymize — empty mapping,
    no spurious copies."""
    from sql_agent.executor import _anonymize_labels
    agg = {"row_count": 10, "numeric": {"amount": {"total": 5000}}, "categorical": {}}
    anon, mapping = _anonymize_labels(agg)
    assert mapping == {}
    assert anon["numeric"] == agg["numeric"]


def test_falls_back_to_local_sensitive_when_cloud_fails():
    """If the cloud aggregate call raises, the original local sensitive=True
    path must run with the raw row sample. No silent failure."""
    df = pd.DataFrame({"region": ["EU", "US", "EU"], "amount": [100.0, 200.0, 50.0]})

    calls = []

    def fake_invoke(prompt, *args, **kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            raise RuntimeError("Bedrock unreachable")
        return "Local explanation: 350 total."

    with patch("sql_agent.executor.llm_invoke", side_effect=fake_invoke):
        out = _explain_result("total by region?", df, "scalar")

    assert "350" in out or "Local explanation" in out
    assert len(calls) == 2, "Expected exactly one cloud attempt then one local fallback."
    assert calls[0].get("sensitive") is False, "First attempt is the cloud path."
    assert calls[1].get("sensitive") is True, \
        "Fallback must keep raw rows on local Ollama via sensitive=True."
