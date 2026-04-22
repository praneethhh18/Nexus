"""
PDF Report Builder — generates professional PDF reports using ReportLab.
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd
from loguru import logger

from config.settings import REPORTS_DIR

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable,
)

# Color palette
NEXUS_BLUE = colors.HexColor("#1e3a5f")
NEXUS_LIGHT = colors.HexColor("#e2e8f0")
ACCENT = colors.HexColor("#3b82f6")
ALT_ROW = colors.HexColor("#f8fafc")
WHITE = colors.white
DARK = colors.HexColor("#0f172a")


def _footer(canvas, doc):
    """Draw footer on every page."""
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.grey)
    canvas.drawString(2 * cm, 1 * cm, f"NexusAgent Report  •  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    canvas.drawRightString(A4[0] - 2 * cm, 1 * cm, f"Page {doc.page}")
    canvas.restoreState()


def _df_to_table_data(df: pd.DataFrame, max_rows: int = 25) -> list:
    """Convert DataFrame to ReportLab table data."""
    if df.empty:
        return [["No data available"]]
    display_df = df.head(max_rows)
    headers = list(display_df.columns)
    rows = []
    for _, row in display_df.iterrows():
        rows.append([str(v) for v in row.values])
    return [headers] + rows


def build_pdf(
    title: str,
    executive_summary: str,
    dataframe: pd.DataFrame,
    chart_image_path: Optional[str],
    key_insights: List[str],
    subtitle: str = "",
) -> str:
    """
    Generate a professional PDF report.

    Returns: path to generated PDF file.
    """
    Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40].strip()
    out_path = Path(REPORTS_DIR) / f"report_{safe_title}_{timestamp}.pdf"

    doc = SimpleDocTemplate(
        str(out_path),
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2.5 * cm,
        bottomMargin=2.5 * cm,
    )

    styles = getSampleStyleSheet()
    style_body = styles["BodyText"]
    style_body.spaceAfter = 6

    title_style = ParagraphStyle(
        "TitleStyle",
        parent=styles["Title"],
        textColor=NEXUS_BLUE,
        fontSize=24,
        spaceAfter=6,
    )
    h1_style = ParagraphStyle(
        "H1", parent=styles["Heading1"],
        textColor=NEXUS_BLUE, fontSize=14, spaceAfter=8,
    )
    h2_style = ParagraphStyle(
        "H2", parent=styles["Heading2"],
        textColor=ACCENT, fontSize=11, spaceAfter=6,
    )
    bullet_style = ParagraphStyle(
        "Bullet", parent=style_body,
        leftIndent=20, bulletIndent=10, spaceAfter=4,
    )

    story = []

    # ── Cover Page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("NexusAgent", ParagraphStyle(
        "Brand", parent=styles["Title"], textColor=ACCENT, fontSize=32,
    )))
    story.append(Spacer(1, 0.5 * cm))
    story.append(HRFlowable(width="100%", thickness=2, color=NEXUS_BLUE))
    story.append(Spacer(1, 0.3 * cm))
    story.append(Paragraph(title, title_style))
    if subtitle:
        story.append(Paragraph(subtitle, styles["Italic"]))
    story.append(Spacer(1, 0.5 * cm))
    story.append(Paragraph(
        f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}",
        styles["Normal"],
    ))
    story.append(PageBreak())

    # ── Executive Summary ─────────────────────────────────────────────────────
    story.append(Paragraph("Executive Summary", h1_style))
    story.append(HRFlowable(width="100%", thickness=1, color=NEXUS_LIGHT))
    story.append(Spacer(1, 0.2 * cm))
    for para in executive_summary.split("\n\n"):
        if para.strip():
            story.append(Paragraph(para.strip(), style_body))
            story.append(Spacer(1, 0.2 * cm))

    story.append(Spacer(1, 0.5 * cm))

    # ── Chart ─────────────────────────────────────────────────────────────────
    if chart_image_path and Path(chart_image_path).exists():
        story.append(Paragraph("Data Visualization", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=NEXUS_LIGHT))
        story.append(Spacer(1, 0.2 * cm))
        img_width = 16 * cm
        img = Image(chart_image_path, width=img_width, height=img_width * 0.55)
        story.append(img)
        story.append(Spacer(1, 0.5 * cm))

    # ── Data Table ────────────────────────────────────────────────────────────
    if dataframe is not None and not dataframe.empty:
        story.append(Paragraph("Data Table", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=NEXUS_LIGHT))
        story.append(Spacer(1, 0.2 * cm))

        table_data = _df_to_table_data(dataframe, max_rows=20)
        n_cols = len(table_data[0])
        col_width = (A4[0] - 4 * cm) / n_cols

        tbl = Table(table_data, colWidths=[col_width] * n_cols, repeatRows=1)
        row_styles = []
        for r in range(1, len(table_data)):
            bg = ALT_ROW if r % 2 == 0 else WHITE
            row_styles.append(("BACKGROUND", (0, r), (-1, r), bg))

        tbl.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NEXUS_BLUE),
            ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 9),
            ("ALIGN", (0, 0), (-1, -1), "LEFT"),
            ("FONTSIZE", (0, 1), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, ALT_ROW]),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            *row_styles,
        ]))
        story.append(tbl)
        story.append(Spacer(1, 0.5 * cm))

    # ── Key Insights ──────────────────────────────────────────────────────────
    if key_insights:
        story.append(Paragraph("Key Insights", h1_style))
        story.append(HRFlowable(width="100%", thickness=1, color=NEXUS_LIGHT))
        story.append(Spacer(1, 0.2 * cm))
        for insight in key_insights:
            story.append(Paragraph(f"• {insight}", bullet_style))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc.build(story, onFirstPage=_footer, onLaterPages=_footer)
    logger.success(f"[PDFBuilder] Report saved: {out_path.name}")
    return str(out_path)
