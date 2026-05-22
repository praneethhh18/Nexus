"""End-to-end report pipeline: natural-language question -> PDF on disk.

Lives outside `api/server.py` so:
  - the endpoint stays a thin shim (auth + body parsing only)
  - the pipeline is unit-testable without an HTTP client
  - someone wiring a workflow node or a scheduled report can call
    `generate_report_pdf(...)` directly

Pipeline:
    NL question
      -> sql_agent.execute_query   (NL -> SQL -> dataframe)
      -> chart_selector            (pick best chart type for shape)
      -> chart_builder             (Plotly PNG)
      -> narrative.generate_narrative  (aggregate + cloud LLM prose)
      -> pdf_builder.build_pdf     (ReportLab assembly)

Each step is best-effort: if chart or narrative degrades we still
ship the PDF with the data table and whatever sections survived.
SQL failure / empty result is fatal (returns the error so the caller
can show a helpful 422).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Any

from loguru import logger


# Verbs we want to strip from the start of the title so it reads like
# a headline ("Top 2 customers by revenue") rather than a command
# ("Generate a report on top 2 customers by revenue").
_TITLE_VERB_PREFIX = re.compile(
    r"^(generate|show|build|create|give|make)\s+(me\s+)?(a\s+|an\s+|the\s+)?"
    r"(report\s+(on|of|about|for)\s+)?",
    re.IGNORECASE,
)


def _build_title(question: str) -> str:
    """Turn 'Generate a report on top 5 customers' into 'Top 5 customers'."""
    cleaned = _TITLE_VERB_PREFIX.sub("", question or "").strip()
    return cleaned.capitalize()[:80] or "Custom report"


def _select_chart(df, question: str) -> str:
    from report_generator.chart_selector import select_chart_type
    try:
        chart_type, _reason = select_chart_type(df, question)
        return chart_type
    except Exception as e:
        logger.warning(f"[reports] chart selection failed: {e}")
        return "table"


def _build_chart_png(df, chart_type: str, title: str):
    if chart_type == "table":
        return None
    from report_generator.chart_builder import build_chart
    try:
        _fig, png = build_chart(df, chart_type, title=title, save=True)
        return png
    except Exception as e:
        logger.warning(f"[reports] chart build failed: {e}")
        return None


def _narrative_or_fallback(question: str, df) -> Dict[str, Any]:
    """Try the cloud narrative; degrade to an empty-sections payload
    that the PDF builder can still render."""
    from report_generator.narrative import generate_narrative
    try:
        return generate_narrative(question, df)
    except Exception as e:
        logger.warning(f"[reports] narrative failed: {e}")
        return {
            "narrative": "",
            "sections": {"summary": "", "metrics": [], "breakdown": "", "recommendation": ""},
            "aggregates": {"row_count": len(df), "column_count": len(df.columns)},
            "mode": "error",
        }


def _compose_pdf_inputs(narrative: Dict[str, Any], df) -> tuple[str, list[str]]:
    """Map the structured narrative sections onto the two PDF slots the
    builder consumes today: an executive_summary paragraph and a list
    of key_insights bullets.

    PDF only has one prose slot, so we merge the optional Breakdown
    into the executive summary. Recommendations get appended to the
    insights list so the user sees the 'so what' at the bottom."""
    sections = narrative.get("sections") or {}

    executive_summary = (sections.get("summary") or "").strip()
    if not executive_summary:
        executive_summary = (
            f"This report covers {len(df)} records across {len(df.columns)} fields."
        )

    breakdown = (sections.get("breakdown") or "").strip()
    if breakdown:
        executive_summary = f"{executive_summary}\n\n{breakdown}".strip()

    key_insights: list[str] = []
    for m in sections.get("metrics") or []:
        if m and m.strip():
            key_insights.append(m.strip())

    rec = (sections.get("recommendation") or "").strip()
    if rec:
        for ln in rec.split("\n"):
            ln = ln.lstrip("- ").strip()
            if ln:
                key_insights.append(ln)

    return executive_summary, key_insights[:8]


class ReportError(Exception):
    """Raised when the pipeline can't produce a meaningful report.
    Caller (FastAPI endpoint) maps to HTTP 422 / 500."""
    def __init__(self, message: str, *, kind: str = "failed", sql: str = ""):
        super().__init__(message)
        self.kind = kind   # 'empty' | 'sql_error' | 'failed'
        self.sql = sql


def generate_report_pdf(question: str, business_id: str) -> str:
    """Run the full pipeline and return the path to the generated PDF.

    Raises ReportError when there's no data or the SQL agent can't
    produce a query for the question.
    """
    from sql_agent.executor import execute_query
    from sql_agent.query_generator import clear_cache as clear_sql_cache
    from report_generator.pdf_builder import build_pdf

    if not (question and question.strip()):
        raise ReportError("query is required", kind="failed")

    # Fresh SQL each request so a previously cached, dialect-wrong
    # query doesn't stick around once we've fixed the prompt.
    clear_sql_cache()

    try:
        sql_result = execute_query(question, business_id=business_id)
    except Exception as e:
        logger.exception(f"[reports] SQL execution failed: {e}")
        raise ReportError(f"Could not query the data: {e}", kind="sql_error")

    df = sql_result.get("dataframe")
    if df is None or getattr(df, "empty", True):
        sql_used = sql_result.get("query_used") or "(no SQL generated)"
        sql_error = sql_result.get("error") or "the query returned no rows"
        logger.warning(
            f"[reports] empty/failed for question={question!r} | "
            f"sql={sql_used[:200]!r} | error={sql_error!r}"
        )
        raise ReportError(
            f"I couldn't pull data for that question. Reason: {sql_error}. "
            f"Try rephrasing or naming the entity explicitly "
            f"(e.g. 'top 5 customers by total invoice amount this quarter').",
            kind="empty", sql=sql_used,
        )

    title = _build_title(question)
    chart_type = _select_chart(df, question)
    chart_path = _build_chart_png(df, chart_type, title)
    narrative = _narrative_or_fallback(question, df)
    executive_summary, key_insights = _compose_pdf_inputs(narrative, df)

    try:
        pdf_path = build_pdf(
            title=title,
            executive_summary=executive_summary,
            dataframe=df,
            chart_image_path=chart_path,
            key_insights=key_insights,
            subtitle=f"Generated from: {question[:120]}",
        )
    except Exception as e:
        logger.exception(f"[reports] PDF build failed: {e}")
        raise ReportError(f"Could not assemble the PDF: {e}", kind="failed")

    if not pdf_path or not Path(pdf_path).exists():
        raise ReportError("Report generation failed", kind="failed")
    return pdf_path
