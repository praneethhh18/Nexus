"""
Data helpers — pandas utilities for NexusAgent.
"""
from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def format_currency(value: float, symbol: str = "$") -> str:
    return f"{symbol}{value:,.2f}"


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    if denominator == 0:
        return default
    return numerator / denominator


def top_n_by_column(df: pd.DataFrame, value_col: str, n: int = 10,
                    ascending: bool = False) -> pd.DataFrame:
    return df.nlargest(n, value_col) if not ascending else df.nsmallest(n, value_col)


def pivot_summary(df: pd.DataFrame, index: str, columns: str, values: str,
                  aggfunc: str = "sum") -> pd.DataFrame:
    try:
        return df.pivot_table(index=index, columns=columns, values=values,
                               aggfunc=aggfunc, fill_value=0)
    except Exception:
        return df


def df_to_dict_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
    return df.to_dict(orient="records") if not df.empty else []
