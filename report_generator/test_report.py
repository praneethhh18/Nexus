"""
Report Generator Test — creates a sample PDF from mock data.
Run: python report_generator/test_report.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import pandas as pd
from config.settings import ensure_directories

SAMPLE_DATA = {
    "region": ["North", "South", "East", "West", "Central"],
    "revenue": [125000, 89000, 142000, 76000, 98000],
    "units_sold": [320, 215, 410, 180, 255],
    "growth_pct": [12.3, -5.2, 18.7, 3.1, 8.9],
}

INSIGHTS = [
    "East region leads with $142,000 revenue and 18.7% growth",
    "South region declined 5.2% — requires sales intervention",
    "North and Central show steady 8-12% growth",
    "Overall portfolio revenue: $530,000 with average 7.6% growth",
]

SUMMARY = """
This quarterly analysis covers all five regional business units for Q3 2025.
The East region continues to outperform targets driven by enterprise contract wins.

The South region decline warrants immediate attention from regional management.
Recommended actions include a focused sales push and customer retention program.

Overall business health remains strong with four of five regions posting positive growth.
"""


def main():
    ensure_directories()
    df = pd.DataFrame(SAMPLE_DATA)

    # Build chart
    from report_generator.chart_selector import select_chart_type
    from report_generator.chart_builder import build_chart

    chart_type, reason = select_chart_type(df, "Regional revenue and growth comparison")
    print(f"Chart type selected: {chart_type} — {reason}")

    fig, png_path = build_chart(df, chart_type, "Q3 Regional Revenue", save=True)
    print(f"Chart saved: {png_path}")

    # Build PDF
    from report_generator.pdf_builder import build_pdf

    pdf_path = build_pdf(
        title="Q3 2025 Regional Business Review",
        executive_summary=SUMMARY,
        dataframe=df,
        chart_image_path=png_path,
        key_insights=INSIGHTS,
        subtitle="NexusAgent Auto-Generated Report",
    )

    print(f"\nPDF Report: {pdf_path}")
    print("TEST PASSED — Report generated successfully")


if __name__ == "__main__":
    main()
