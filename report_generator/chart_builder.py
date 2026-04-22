"""
Chart Builder — builds Plotly charts from DataFrames and saves as PNG.
"""
from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from loguru import logger

from config.settings import REPORTS_DIR

PALETTE = px.colors.qualitative.Plotly
MAX_PIE_SLICES = 8


def _collapse_small_categories(df: pd.DataFrame, label_col: str,
                                value_col: str, max_cats: int = MAX_PIE_SLICES) -> pd.DataFrame:
    """Group smallest categories into 'Other' if there are too many."""
    if len(df) <= max_cats:
        return df
    top = df.nlargest(max_cats - 1, value_col)
    other_val = df[value_col].sum() - top[value_col].sum()
    other_row = pd.DataFrame({label_col: ["Other"], value_col: [other_val]})
    return pd.concat([top, other_row], ignore_index=True)


def build_chart(
    df: pd.DataFrame,
    chart_type: str,
    title: str,
    save: bool = True,
) -> Tuple[Optional[go.Figure], Optional[str]]:
    """
    Build a Plotly chart and optionally save as PNG.

    Returns:
        (fig: plotly Figure | None, png_path: str | None)
    """
    if df is None or df.empty:
        logger.warning("[ChartBuilder] Empty DataFrame — no chart built.")
        return None, None

    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    str_cols = df.select_dtypes(exclude="number").columns.tolist()

    if not numeric_cols:
        logger.warning("[ChartBuilder] No numeric columns — cannot build chart.")
        return None, None

    x_col = str_cols[0] if str_cols else df.columns[0]
    y_col = numeric_cols[0]

    try:
        if chart_type == "bar":
            if len(df) > 30:
                df = df.nlargest(20, y_col)
            fig = px.bar(df, x=x_col, y=y_col, title=title,
                         color_discrete_sequence=PALETTE,
                         text_auto=".2s")
            fig.update_traces(textposition="outside")

        elif chart_type == "line":
            fig = px.line(df, x=x_col, y=numeric_cols[:3], title=title,
                          markers=True, color_discrete_sequence=PALETTE)

        elif chart_type == "pie":
            df_pie = _collapse_small_categories(df, x_col, y_col)
            fig = px.pie(df_pie, names=x_col, values=y_col, title=title,
                         color_discrete_sequence=PALETTE,
                         hole=0.35)

        elif chart_type == "scatter":
            y2_col = numeric_cols[1] if len(numeric_cols) > 1 else y_col
            fig = px.scatter(df, x=y_col, y=y2_col, title=title,
                             hover_data=df.columns[:4].tolist(),
                             color_discrete_sequence=PALETTE)

        else:
            # Table fallback
            fig = go.Figure(data=[go.Table(
                header=dict(
                    values=list(df.columns),
                    fill_color="#1f77b4",
                    font=dict(color="white", size=12),
                    align="left",
                ),
                cells=dict(
                    values=[df[c].tolist() for c in df.columns],
                    fill_color=[["#f0f0f0", "white"] * len(df)],
                    align="left",
                ),
            )])
            fig.update_layout(title_text=title)

        # Professional styling
        fig.update_layout(
            template="plotly_white",
            title_font_size=16,
            font=dict(family="Arial, sans-serif", size=12),
            margin=dict(l=40, r=40, t=60, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )

        png_path = None
        if save:
            Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40]
            fname = Path(REPORTS_DIR) / f"chart_{safe_title}_{timestamp}.png"
            try:
                fig.write_image(str(fname), width=900, height=500, scale=2)
                png_path = str(fname)
                logger.success(f"[ChartBuilder] Saved: {fname.name}")
            except Exception as e:
                logger.warning(f"[ChartBuilder] PNG save failed (kaleido?): {e}")

        return fig, png_path

    except Exception as e:
        logger.error(f"[ChartBuilder] Chart build failed: {e}")
        return None, None
