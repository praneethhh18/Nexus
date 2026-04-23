"""
Narrative report generator — aggregate-then-cloud.

Reports benefit from cloud-quality prose (Nova Pro / Claude) but sending raw
rows to the cloud would leak customer/business data. This module splits the
work:

    1. Aggregate locally — compute totals, averages, top-N, trends, category
       breakdowns from the DataFrame. No rows leave this machine.
    2. Redact aggregate labels — category labels may still contain PII
       (customer names, vendor names). The privacy layer scrubs them before
       the cloud call, and restores them in the final narrative.
    3. Cloud narrative — only the numeric aggregates + redacted labels go to
       the cloud LLM, which writes a polished executive narrative.
    4. Local fallback — if cloud is disabled or the kill-switch is on, we
       degrade gracefully to Ollama.

The goal: 360° business automation with cloud-quality writing on local-only
data. Individual rows — invoice numbers, customer emails, raw transactions —
never traverse the network boundary.
"""
from __future__ import annotations

from typing import Dict, Any, List
import pandas as pd
from loguru import logger

from config.llm_provider import invoke as llm_invoke


# ── Local aggregation ──────────────────────────────────────────────────────
def _numeric_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _categorical_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns
            if not pd.api.types.is_numeric_dtype(df[c])
            and not pd.api.types.is_datetime64_any_dtype(df[c])]


def compute_aggregates(df: pd.DataFrame, max_groups: int = 5) -> Dict[str, Any]:
    """
    Reduce a DataFrame to a small, cloud-safe summary: row count, numeric
    totals / means / min / max, and top-N values for each categorical column.
    """
    if df is None or df.empty:
        return {"row_count": 0, "numeric": {}, "categorical": {}, "note": "no data"}

    agg: Dict[str, Any] = {
        "row_count": int(len(df)),
        "column_count": int(len(df.columns)),
        "numeric": {},
        "categorical": {},
    }

    for col in _numeric_cols(df):
        series = df[col].dropna()
        if series.empty:
            continue
        agg["numeric"][col] = {
            "total": round(float(series.sum()), 2),
            "mean":  round(float(series.mean()), 2),
            "min":   round(float(series.min()), 2),
            "max":   round(float(series.max()), 2),
        }

    for col in _categorical_cols(df):
        counts = df[col].astype(str).value_counts().head(max_groups)
        if counts.empty:
            continue
        agg["categorical"][col] = [
            {"label": str(label), "count": int(n)} for label, n in counts.items()
        ]
        # If there's one "primary" numeric column, also break it down by this category
        numeric = _numeric_cols(df)
        if numeric:
            primary = numeric[0]
            top = (
                df.groupby(col, dropna=False)[primary]
                .sum()
                .sort_values(ascending=False)
                .head(max_groups)
            )
            agg["categorical"][col + "_by_" + primary] = [
                {"label": str(label), primary: round(float(val), 2)}
                for label, val in top.items()
            ]

    return agg


# ── Cloud narrative ─────────────────────────────────────────────────────────
_NARRATIVE_SYSTEM = (
    "You are a senior business analyst writing an executive report. "
    "You receive ONLY aggregated figures — never raw rows. Write clear, "
    "confident prose that a CEO would read. Use the numbers provided. "
    "Do not invent figures. Do not speculate beyond the data. Keep paragraphs "
    "short (2-3 sentences)."
)


def _build_narrative_prompt(query: str, aggregates: Dict[str, Any]) -> str:
    import json
    return (
        f"Business question: {query}\n\n"
        f"Aggregated data (totals, means, top categories):\n"
        f"{json.dumps(aggregates, default=str, indent=2)}\n\n"
        "Write an executive report with these sections:\n"
        "  1. **Executive Summary** — 3 sentences, the headline finding.\n"
        "  2. **Key Metrics** — 3-5 bullet points on the most important numbers.\n"
        "  3. **Breakdown** — one paragraph per significant categorical split.\n"
        "  4. **Recommendation** — 2 sentences on what action to take next.\n\n"
        "Use Markdown. Format money with currency symbol and commas. "
        "Reference specific numbers from the aggregates above."
    )


def generate_narrative(query: str, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Full pipeline: local aggregation → cloud narrative → returns the
    narrative text plus the aggregates so the PDF builder can render both.

    The call is `sensitive=False` because we've stripped to aggregates first —
    no individual records are in the payload. The privacy layer still redacts
    any PII that slipped into category labels (e.g. customer names used as
    group keys) and restores them in the returned narrative.
    """
    aggregates = compute_aggregates(df)

    if aggregates["row_count"] == 0:
        return {
            "narrative": "_No data available to report on._",
            "aggregates": aggregates,
            "mode": "empty",
        }

    prompt = _build_narrative_prompt(query, aggregates)
    try:
        narrative = llm_invoke(
            prompt,
            system=_NARRATIVE_SYSTEM,
            max_tokens=1200,
            temperature=0.2,
            sensitive=False,  # aggregates only — no raw rows in payload
        )
        return {"narrative": narrative.strip(), "aggregates": aggregates, "mode": "cloud"}
    except Exception as e:
        logger.warning(f"[Narrative] Cloud narrative failed, falling back to local: {e}")
        # Local fallback — short insight only, still uses the aggregates
        try:
            local = llm_invoke(
                prompt,
                system=_NARRATIVE_SYSTEM,
                max_tokens=512,
                sensitive=True,
            )
            return {"narrative": local.strip(), "aggregates": aggregates, "mode": "local-fallback"}
        except Exception as e2:
            logger.error(f"[Narrative] Local fallback also failed: {e2}")
            return {
                "narrative": f"Report covers {aggregates['row_count']} records across "
                             f"{aggregates['column_count']} fields.",
                "aggregates": aggregates,
                "mode": "static-fallback",
            }


def short_summary(query: str, df: pd.DataFrame) -> str:
    """Convenience: return just the narrative text (for PDF exec-summary block)."""
    return generate_narrative(query, df)["narrative"]
