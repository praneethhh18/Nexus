"""
What-If Scenario Simulator — models business scenarios and critiques assumptions.
"""
from __future__ import annotations

import re
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
from loguru import logger

from config.settings import DB_PATH
from config.llm_config import get_llm


def parse_scenario(query: str) -> Dict[str, Any]:
    """
    Use local LLM to extract scenario parameters from a natural language query.

    Returns:
        {metric, change_pct, secondary_metric, secondary_change_pct, description}
    """
    llm = get_llm()
    prompt = f"""Extract the scenario parameters from this what-if question.

Question: "{query}"

Reply ONLY with this format:
METRIC: <revenue|units_sold|returns|customers>
CHANGE_PCT: <positive or negative number, e.g. -20 or +10>
SECONDARY_METRIC: <another metric or NONE>
SECONDARY_CHANGE_PCT: <number or 0>
DESCRIPTION: <one sentence describing the scenario>"""

    try:
        response = llm.invoke(prompt)
        lines = response.strip().split("\n")
        result = {
            "metric": "revenue",
            "change_pct": -10.0,
            "secondary_metric": None,
            "secondary_change_pct": 0.0,
            "description": query,
        }
        for line in lines:
            if ":" not in line:
                continue
            key, val = line.split(":", 1)
            key = key.strip().upper()
            val = val.strip()
            if key == "METRIC":
                result["metric"] = val.lower()
            elif key == "CHANGE_PCT":
                nums = re.findall(r"[-+]?\d+\.?\d*", val)
                if nums:
                    result["change_pct"] = float(nums[0])
            elif key == "SECONDARY_METRIC" and val.upper() != "NONE":
                result["secondary_metric"] = val.lower()
            elif key == "SECONDARY_CHANGE_PCT":
                nums = re.findall(r"[-+]?\d+\.?\d*", val)
                if nums:
                    result["secondary_change_pct"] = float(nums[0])
            elif key == "DESCRIPTION":
                result["description"] = val
        return result
    except Exception as e:
        logger.error(f"[WhatIf] parse_scenario failed: {e}")
        return {
            "metric": "revenue",
            "change_pct": -10.0,
            "secondary_metric": None,
            "secondary_change_pct": 0.0,
            "description": query,
        }


def run_simulation(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Apply the scenario mathematically to current database data.
    Returns before/after metrics.
    """
    metric = scenario.get("metric", "revenue")
    change_pct = scenario.get("change_pct", 0.0) / 100.0
    secondary_metric = scenario.get("secondary_metric")
    secondary_change_pct = scenario.get("secondary_change_pct", 0.0) / 100.0

    try:
        conn = sqlite3.connect(DB_PATH)
        # The simulator only runs against the seed-data tables (orders /
        # sales_metrics). On a fresh business those tables can be missing
        # entirely or empty — fall through to a clear, actionable error
        # rather than silently returning zeros which look like a UI bug.
        def _table_exists(name: str) -> bool:
            row = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
            ).fetchone()
            return row is not None

        if not _table_exists("orders") or not _table_exists("sales_metrics"):
            conn.close()
            return {"error": (
                "What-If needs the sample sales tables to model scenarios. Click "
                "\"Load sample data\" on the dashboard, then try again."
            )}

        # Get current totals from orders/sales
        df_orders = pd.read_sql_query(
            "SELECT region, SUM(total_amount) as revenue, COUNT(*) as orders FROM orders GROUP BY region",
            conn
        )
        df_metrics = pd.read_sql_query(
            "SELECT region, SUM(revenue) as revenue, SUM(units_sold) as units_sold, "
            "SUM(returns) as returns FROM sales_metrics WHERE metric_type='daily' GROUP BY region",
            conn
        )

        if df_orders.empty and df_metrics.empty:
            conn.close()
            return {"error": (
                "No orders or sales metrics rows found yet. Add data, or load "
                "the sample data from the dashboard, then try again."
            )}
        conn.close()

        if df_metrics.empty:
            df_metrics = df_orders.rename(columns={"revenue": "revenue"})
            df_metrics["units_sold"] = 0
            df_metrics["returns"] = 0

        before = df_metrics.copy()
        after = df_metrics.copy()

        # Apply primary change
        if metric in after.columns:
            after[metric] = after[metric] * (1 + change_pct)

        # Apply secondary change
        if secondary_metric and secondary_metric in after.columns and secondary_change_pct:
            after[secondary_metric] = after[secondary_metric] * (1 + secondary_change_pct)

        # Net impact
        if "revenue" in before.columns and "revenue" in after.columns:
            before_total = before["revenue"].sum()
            after_total = after["revenue"].sum()
            net_impact_abs = after_total - before_total
            net_impact_pct = (net_impact_abs / before_total * 100) if before_total else 0
        else:
            before_total = after_total = net_impact_abs = net_impact_pct = 0

        return {
            "before": before,
            "after": after,
            "before_total_revenue": round(before_total, 2),
            "after_total_revenue": round(after_total, 2),
            "net_impact_abs": round(net_impact_abs, 2),
            "net_impact_pct": round(net_impact_pct, 2),
        }

    except Exception as e:
        logger.error(f"[WhatIf] run_simulation failed: {e}")
        return {"error": str(e)}


def generate_comparison(before: pd.DataFrame, after: pd.DataFrame,
                        title: str = "What-If Analysis") -> Optional[str]:
    """Create a side-by-side Plotly bar chart comparing before vs after."""
    try:
        from report_generator.chart_builder import build_chart
        import plotly.graph_objects as go
        from pathlib import Path
        from config.settings import REPORTS_DIR

        Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
        if "region" not in before.columns or "revenue" not in before.columns:
            return None

        regions = before["region"].tolist()
        fig = go.Figure(data=[
            go.Bar(name="Before", x=regions, y=before["revenue"].tolist(),
                   marker_color="#3498db"),
            go.Bar(name="After", x=regions, y=after["revenue"].tolist(),
                   marker_color="#e74c3c"),
        ])
        fig.update_layout(
            title_text=title,
            barmode="group",
            template="plotly_white",
            font=dict(family="Arial", size=12),
        )

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        png_path = str(Path(REPORTS_DIR) / f"whatif_{timestamp}.png")
        try:
            fig.write_image(png_path, width=900, height=500, scale=2)
        except Exception:
            png_path = None

        return png_path
    except Exception as e:
        logger.error(f"[WhatIf] generate_comparison failed: {e}")
        return None


def critique_simulation(scenario: Dict[str, Any], result: Dict[str, Any]) -> str:
    """Ask LLM to critique the assumptions and flag risks."""
    try:
        llm = get_llm()
        prompt = f"""You are a CFO reviewing a business scenario simulation. Critique the assumptions.

SCENARIO: {scenario.get('description', 'Unknown')}
CHANGE: {scenario.get('metric')} {scenario.get('change_pct')}%
NET REVENUE IMPACT: ${result.get('net_impact_abs', 0):,.0f} ({result.get('net_impact_pct', 0):.1f}%)

List 3 key assumptions that may be incorrect, and 2 risks to watch.
Be concise — 2-3 sentences total."""

        return llm.invoke(prompt).strip()
    except Exception as e:
        return f"Critique unavailable: {e}"


def run_full_simulation(query: str) -> Dict[str, Any]:
    """
    Full what-if pipeline: parse → simulate → chart → critique.
    Returns a comprehensive result dict.

    Data source: this simulator currently reads from the global `orders` and
    `sales_metrics` tables (the bundled demo dataset). It is NOT yet scoped
    to the caller's business — every business sees numbers off the same
    seed data. The result is tagged with `data_source` so the frontend
    can surface this honestly to the user. Tenant-scoped simulation against
    `nexus_invoices` is a follow-up.
    """
    scenario = parse_scenario(query)
    logger.info(f"[WhatIf] Scenario: {scenario}")

    sim_result = run_simulation(scenario)
    if "error" in sim_result:
        return {
            "error": sim_result["error"],
            "scenario_description": scenario.get("description"),
            "data_source": "sample_dataset",
        }

    chart_path = generate_comparison(
        sim_result["before"], sim_result["after"],
        title=f"What-If: {scenario['description'][:60]}"
    )
    critique = critique_simulation(scenario, sim_result)

    net = sim_result.get("net_impact_abs", 0)
    net_pct = sim_result.get("net_impact_pct", 0)
    direction = "increase" if net >= 0 else "decrease"

    return {
        "scenario_description": scenario.get("description"),
        "metric": scenario.get("metric"),
        "change_pct": scenario.get("change_pct"),
        "before_total_revenue": sim_result.get("before_total_revenue"),
        "after_total_revenue": sim_result.get("after_total_revenue"),
        "net_impact": f"${abs(net):,.0f} {direction} ({abs(net_pct):.1f}%)",
        "net_impact_abs": net,
        "net_impact_pct": net_pct,
        "chart_path": chart_path,
        "assumptions": f"This simulation assumes a direct linear {direction} in {scenario['metric']}.",
        "critique": critique,
        "confidence": 0.75,
        # See module docstring — currently always the bundled demo data, not
        # the caller's business. Frontend should surface this to the user.
        "data_source": "sample_dataset",
        "before_df": sim_result["before"],
        "after_df": sim_result["after"],
    }
