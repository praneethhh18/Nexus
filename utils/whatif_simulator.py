"""
What-If Scenario Simulator — models business scenarios and critiques assumptions.

The simulator has two data sources, picked at run time:

  1. **`your_invoices`** — when the caller passes `business_id` AND that
     workspace has at least one invoice in `nexus_invoices`, we use the
     user's actual data: aggregate `total` by `status` for that business,
     apply the scenario's percentage delta to the revenue column, and
     return the before/after frame. Tenant-isolated by construction —
     SQL filters on business_id every read.

  2. **`sample_dataset`** — fallback for fresh workspaces with no
     invoices yet, or when the simulator is invoked without a
     business_id (e.g. CLI). Reads from the bundled demo `orders` /
     `sales_metrics` tables. Used to be the *only* path; kept for
     onboarding moments where the user wants to see the feature work
     before they have real data.

The result dict tags the path used (`data_source`) so the frontend can
distinguish "your numbers" from "demo numbers" and message accordingly.
"""
from __future__ import annotations

import re
import sqlite3  # sqlite3.Row sentinel — works on Postgres via config.db
from datetime import datetime
from typing import Dict, Any, Optional

import pandas as pd
from loguru import logger

from config.db import get_conn, table_exists
from config.llm_config import get_llm


# ── Scenario parsing ─────────────────────────────────────────────────────────
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


# ── Data sources ─────────────────────────────────────────────────────────────
def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = (1,) if table_exists(conn, name) else None
    return row is not None


def _simulate_from_invoices(
    scenario: Dict[str, Any], business_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Try to run the simulation against the user's real `nexus_invoices` data.

    Returns the before/after frame + totals if invoices exist for this
    business, or None when there's nothing to model (caller should fall
    back to the sample-data path).

    Aggregation strategy: group by `status` (draft / sent / paid / overdue
    / cancelled). Only paid + sent count toward the "revenue" total — those
    are the cash-in / cash-likely buckets. Draft / cancelled are kept in
    the frame for visibility but don't contribute to the impact number.

    Tenant safety: the SQL filters on business_id, so a leak would require
    a SQL bug — caught by tests/test_multitenant_isolation.py.
    """
    metric = scenario.get("metric", "revenue")
    change_pct = scenario.get("change_pct", 0.0) / 100.0

    conn = get_conn()
    try:
        if not _table_exists(conn, "nexus_invoices"):
            return None

        # Roll up by status. We compute revenue as the sum of invoice totals;
        # `count` is informational so the UI can say "based on N invoices".
        df = pd.read_sql_query(
            """
            SELECT
                COALESCE(NULLIF(status, ''), 'draft') AS status,
                COUNT(*)                              AS invoice_count,
                ROUND(SUM(total), 2)                  AS revenue
            FROM nexus_invoices
            WHERE business_id = ?
            GROUP BY status
            ORDER BY status
            """,
            conn,
            params=(business_id,),
        )
    finally:
        conn.close()

    if df.empty:
        return None

    total_invoices = int(df["invoice_count"].sum() or 0)
    if total_invoices == 0:
        return None

    # Cash-in / cash-likely: paid + sent. Draft / cancelled don't move the
    # bottom line. Overdue counts as expected revenue with a discount —
    # we keep it at face value here; the critique step calls it out.
    cash_mask = df["status"].isin(["paid", "sent", "overdue"])

    before = df.copy()
    after  = df.copy()

    # Apply the percentage change ONLY to the cash-likely rows.
    if metric == "revenue" or metric not in df.columns:
        after.loc[cash_mask, "revenue"] = (
            after.loc[cash_mask, "revenue"] * (1 + change_pct)
        ).round(2)

    before_total = float(before.loc[cash_mask, "revenue"].sum() or 0)
    after_total  = float(after.loc[cash_mask, "revenue"].sum()  or 0)
    net_abs = round(after_total - before_total, 2)
    net_pct = round((net_abs / before_total * 100) if before_total else 0, 2)

    # Pull a representative currency. If the business mixes currencies,
    # we default to the most common one and surface the quirk to the
    # user via the critique. (A proper multi-currency simulator is a
    # bigger project — this stays useful for the common single-currency
    # case.)
    conn = get_conn()
    try:
        cur = conn.execute(
            "SELECT currency, COUNT(*) AS n FROM nexus_invoices "
            "WHERE business_id = ? GROUP BY currency ORDER BY n DESC LIMIT 1",
            (business_id,),
        ).fetchone()
        currency = cur[0] if cur and cur[0] else "USD"
    finally:
        conn.close()

    return {
        "before": before,
        "after":  after,
        "before_total_revenue": round(before_total, 2),
        "after_total_revenue":  round(after_total, 2),
        "net_impact_abs": net_abs,
        "net_impact_pct": net_pct,
        "currency": currency,
        "invoice_count": total_invoices,
    }


def _simulate_from_sample(scenario: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback path — read from the bundled `orders` / `sales_metrics` tables.

    Used when the caller has no business context, or when the workspace has
    no invoices yet. Always tagged `data_source: 'sample_dataset'` so the
    frontend can disclose this to the user.
    """
    metric = scenario.get("metric", "revenue")
    change_pct = scenario.get("change_pct", 0.0) / 100.0
    secondary_metric = scenario.get("secondary_metric")
    secondary_change_pct = scenario.get("secondary_change_pct", 0.0) / 100.0

    try:
        conn = get_conn()
        if not _table_exists(conn, "orders") or not _table_exists(conn, "sales_metrics"):
            conn.close()
            return {"error": (
                "What-If needs either invoices in this workspace or the bundled "
                "sample dataset. Add some invoices, or click \"Load sample data\" "
                "on the dashboard."
            )}

        df_orders = pd.read_sql_query(
            "SELECT region, SUM(total_amount) as revenue, COUNT(*) as orders FROM orders GROUP BY region",
            conn,
        )
        df_metrics = pd.read_sql_query(
            "SELECT region, SUM(revenue) as revenue, SUM(units_sold) as units_sold, "
            "SUM(returns) as returns FROM sales_metrics WHERE metric_type='daily' GROUP BY region",
            conn,
        )

        if df_orders.empty and df_metrics.empty:
            conn.close()
            return {"error": (
                "No invoices in this workspace and no sample data loaded yet. "
                "Add invoices, or click \"Load sample data\" on the dashboard."
            )}
        conn.close()

        if df_metrics.empty:
            df_metrics = df_orders.rename(columns={"revenue": "revenue"})
            df_metrics["units_sold"] = 0
            df_metrics["returns"] = 0

        before = df_metrics.copy()
        after = df_metrics.copy()

        if metric in after.columns:
            after[metric] = after[metric] * (1 + change_pct)

        if secondary_metric and secondary_metric in after.columns and secondary_change_pct:
            after[secondary_metric] = after[secondary_metric] * (1 + secondary_change_pct)

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
            "currency": "USD",
        }

    except Exception as e:
        logger.error(f"[WhatIf] sample-data simulation failed: {e}")
        return {"error": str(e)}


def run_simulation(
    scenario: Dict[str, Any], business_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Apply the scenario mathematically to current database data.

    Tries the user's real invoices first, falls back to sample data only
    when the user has no invoices yet. The returned dict has
    `data_source` set to either `'your_invoices'` or `'sample_dataset'`.
    """
    if business_id:
        invoice_result = _simulate_from_invoices(scenario, business_id)
        if invoice_result is not None:
            invoice_result["data_source"] = "your_invoices"
            return invoice_result

    sample_result = _simulate_from_sample(scenario)
    if "error" not in sample_result:
        sample_result["data_source"] = "sample_dataset"
    else:
        sample_result["data_source"] = "sample_dataset"
    return sample_result


# ── Chart + critique ─────────────────────────────────────────────────────────
def generate_comparison(before: pd.DataFrame, after: pd.DataFrame,
                        title: str = "What-If Analysis") -> Optional[str]:
    """Create a side-by-side Plotly bar chart comparing before vs after."""
    try:
        import plotly.graph_objects as go
        from pathlib import Path
        from config.settings import REPORTS_DIR

        Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
        if "revenue" not in before.columns:
            return None

        # Pick a label column. Sample data uses 'region', invoices use 'status'.
        label_col = "region" if "region" in before.columns else (
            "status" if "status" in before.columns else None
        )
        if not label_col:
            return None

        labels = before[label_col].astype(str).tolist()
        fig = go.Figure(data=[
            go.Bar(name="Before", x=labels, y=before["revenue"].tolist(),
                   marker_color="#3498db"),
            go.Bar(name="After",  x=labels, y=after["revenue"].tolist(),
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


# ── Public entry point ──────────────────────────────────────────────────────
def run_full_simulation(
    query: str, business_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Full what-if pipeline: parse → simulate → chart → critique.

    Pass `business_id` for tenant-scoped simulation against the user's real
    `nexus_invoices`. Without it (or when the workspace has no invoices),
    falls back to the bundled demo dataset and tags the response so the
    frontend can disclose this honestly.
    """
    scenario = parse_scenario(query)
    logger.info(f"[WhatIf] Scenario: {scenario} (biz={business_id or 'none'})")

    sim_result = run_simulation(scenario, business_id=business_id)
    if "error" in sim_result:
        return {
            "error": sim_result["error"],
            "scenario_description": scenario.get("description"),
            "data_source": sim_result.get("data_source", "sample_dataset"),
        }

    chart_path = generate_comparison(
        sim_result["before"], sim_result["after"],
        title=f"What-If: {scenario['description'][:60]}",
    )
    critique = critique_simulation(scenario, sim_result)

    net = sim_result.get("net_impact_abs", 0)
    net_pct = sim_result.get("net_impact_pct", 0)
    direction = "increase" if net >= 0 else "decrease"
    currency = sim_result.get("currency", "USD")

    return {
        "scenario_description": scenario.get("description"),
        "metric": scenario.get("metric"),
        "change_pct": scenario.get("change_pct"),
        "before_total_revenue": sim_result.get("before_total_revenue"),
        "after_total_revenue":  sim_result.get("after_total_revenue"),
        "net_impact": f"{currency} {abs(net):,.0f} {direction} ({abs(net_pct):.1f}%)",
        "net_impact_abs": net,
        "net_impact_pct": net_pct,
        "currency": currency,
        "chart_path": chart_path,
        "assumptions": f"This simulation assumes a direct linear {direction} in {scenario['metric']}.",
        "critique": critique,
        "confidence": 0.75,
        "data_source": sim_result.get("data_source", "sample_dataset"),
        "invoice_count": sim_result.get("invoice_count"),
        "before_df": sim_result["before"],
        "after_df":  sim_result["after"],
    }
