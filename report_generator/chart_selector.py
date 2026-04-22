"""
Chart Selector — uses local LLM to choose the best chart type for a dataset.
"""
from __future__ import annotations

from typing import Tuple

import pandas as pd
from loguru import logger

from config.llm_config import get_llm

CHART_TYPES = {"bar", "line", "pie", "scatter", "table"}


def select_chart_type(df: pd.DataFrame, description: str) -> Tuple[str, str]:
    """
    Decide the best chart type for the given DataFrame and description.

    Returns:
        (chart_type: str, reasoning: str)
        chart_type is one of: bar | line | pie | scatter | table
    """
    # Heuristics for quick fallback (no LLM needed)
    n_rows, n_cols = df.shape
    if n_rows == 0:
        return "table", "Empty dataframe — showing as table."
    if n_cols > 6:
        return "table", "Too many columns for a chart — using table view."

    # Check column types
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    date_like = any(
        "date" in c.lower() or "month" in c.lower() or "week" in c.lower() or "year" in c.lower()
        for c in df.columns
    )

    # Quick heuristic
    if date_like and numeric_cols:
        quick_type = "line"
    elif n_rows <= 7 and n_cols == 2:
        quick_type = "pie"
    elif n_cols == 2 and numeric_cols:
        quick_type = "bar"
    else:
        quick_type = "bar"

    # Ask LLM to confirm / override
    try:
        llm = get_llm()
        col_info = ", ".join(f"{c} ({df[c].dtype})" for c in df.columns)
        prompt = f"""Choose the best chart type for this data.

Data description: {description}
Columns: {col_info}
Rows: {n_rows}
Sample:
{df.head(3).to_string(index=False)}

Answer with EXACTLY one of: bar, line, pie, scatter, table
Then one sentence of reasoning.
Format: CHART_TYPE: <type>\nREASON: <reason>"""

        response = llm.invoke(prompt)
        lines = response.strip().split("\n")
        chart_type = quick_type
        reason = "Auto-selected based on data shape."

        for line in lines:
            if line.upper().startswith("CHART_TYPE:"):
                raw = line.split(":", 1)[1].strip().lower()
                if raw in CHART_TYPES:
                    chart_type = raw
            elif line.upper().startswith("REASON:"):
                reason = line.split(":", 1)[1].strip()

        logger.info(f"[ChartSelector] '{description[:50]}' → {chart_type}")
        return chart_type, reason

    except Exception as e:
        logger.warning(f"[ChartSelector] LLM selection failed, using heuristic: {e}")
        return quick_type, "Heuristic selection (LLM unavailable)."
