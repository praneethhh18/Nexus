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

import re

_FENCE_RE = re.compile(r"```(?:markdown|md|text)?\s*\n?(.*?)\n?```", re.DOTALL)


def _strip_markdown(s: str) -> str:
    """Remove stray markdown so the PDF doesn't show literal ** and ##.
    The narrative prompt asks for plain text but models often slip back
    into markdown habits. This is the safety net before render."""
    if not s:
        return s
    # Peel a wrapping ```...``` fence if the whole reply is wrapped in one.
    m = _FENCE_RE.match(s.strip())
    if m:
        s = m.group(1)
    # Drop heading hashes ('## Foo' -> 'Foo'), keep the text.
    s = re.sub(r"^\s{0,3}#{1,6}\s+", "", s, flags=re.MULTILINE)
    # Drop bold/italic markers but keep the text inside.
    s = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", s)
    s = re.sub(r"\*\*(.+?)\*\*", r"\1", s)
    s = re.sub(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    # Normalize bullets — convert '* ' / '- ' / '• ' at start of line to '- '.
    s = re.sub(r"^[\s]*[\*•]\s+", "- ", s, flags=re.MULTILINE)
    # Replace $ amounts with INR for the Indian SMB audience.
    s = re.sub(r"\$\s?([\d,]+(?:\.\d+)?)", r"INR \1", s)
    s = re.sub(r"\bUSD\b", "INR", s)
    return s.strip()


def parse_sections(narrative: str) -> Dict[str, Any]:
    """Split the LLM narrative into the four labelled sections the PDF
    expects. Falls back to using the whole thing as the executive
    summary when the model ignored the format."""
    sections = {"summary": "", "metrics": [], "breakdown": "", "recommendation": ""}
    if not narrative:
        return sections
    text = _strip_markdown(narrative)

    labels = ["EXECUTIVE SUMMARY", "KEY METRICS", "BREAKDOWN", "RECOMMENDATION"]
    # Build a regex that finds each header and the text that follows it.
    pattern = re.compile(
        r"(?:^|\n)\s*(" + "|".join(labels) + r")\s*\n([\s\S]*?)(?=\n\s*(?:"
        + "|".join(labels) + r")\s*\n|\Z)",
        re.IGNORECASE,
    )
    matches = pattern.findall(text)
    if not matches:
        sections["summary"] = text
        return sections

    for header, body in matches:
        header_norm = header.strip().lower()
        body = body.strip()
        if "summary" in header_norm:
            sections["summary"] = body
        elif "metrics" in header_norm:
            sections["metrics"] = [
                ln.lstrip("- ").strip() for ln in body.splitlines()
                if ln.strip() and ln.strip() != "-"
            ]
        elif "breakdown" in header_norm:
            sections["breakdown"] = body
        elif "recommendation" in header_norm:
            sections["recommendation"] = body
    return sections


# ── Local aggregation ──────────────────────────────────────────────────────
def _numeric_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _categorical_cols(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns
            if not pd.api.types.is_numeric_dtype(df[c])
            and not pd.api.types.is_datetime64_any_dtype(df[c])]


def _indian_comma(n: float) -> str:
    """Format with Indian-style lakh/crore commas."""
    sign = "-" if n < 0 else ""
    n = abs(n)
    integer = int(n)
    s = str(integer)
    if len(s) <= 3:
        out = s
    else:
        last3 = s[-3:]
        rest = s[:-3]
        rest_grouped = ",".join(
            [rest[max(0, i - 2):i] for i in range(len(rest), 0, -2)][::-1]
        )
        out = f"{rest_grouped},{last3}"
    return sign + out


def _money(v: float) -> str:
    """LLM-safe pre-formatted money string. Including this in the payload
    means the model can quote it verbatim instead of guessing at Indian
    number formatting (which it gets wrong half the time)."""
    return f"INR {_indian_comma(v)}"


def compute_aggregates(df: pd.DataFrame, max_groups: int = 5) -> Dict[str, Any]:
    """
    Reduce a DataFrame to a small, cloud-safe summary: row count, numeric
    totals / means / min / max, and top-N values for each categorical column.
    Money-looking columns get a pre-formatted INR string so the LLM
    doesn't have to figure out Indian commas itself.
    """
    if df is None or df.empty:
        return {"row_count": 0, "numeric": {}, "categorical": {}, "note": "no data"}

    money_keywords = (
        "amount", "total", "revenue", "value", "price", "cost",
        "spend", "billed", "paid", "balance", "due", "subtotal", "tax",
    )

    def is_money_col(name: str) -> bool:
        n = name.lower()
        return any(k in n for k in money_keywords)

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
        is_money = is_money_col(col)
        block = {
            "total": round(float(series.sum()), 2),
            "mean":  round(float(series.mean()), 2),
            "min":   round(float(series.min()), 2),
            "max":   round(float(series.max()), 2),
        }
        if is_money:
            block["total_formatted"] = _money(float(series.sum()))
            block["mean_formatted"]  = _money(float(series.mean()))
            block["min_formatted"]   = _money(float(series.min()))
            block["max_formatted"]   = _money(float(series.max()))
        agg["numeric"][col] = block

    for col in _categorical_cols(df):
        counts = df[col].astype(str).value_counts().head(max_groups)
        if counts.empty:
            continue
        agg["categorical"][col] = [
            {"label": str(label), "count": int(n)} for label, n in counts.items()
        ]
        numeric = _numeric_cols(df)
        if numeric:
            primary = numeric[0]
            top = (
                df.groupby(col, dropna=False)[primary]
                .sum()
                .sort_values(ascending=False)
                .head(max_groups)
            )
            is_money = is_money_col(primary)
            agg["categorical"][col + "_by_" + primary] = [
                {
                    "label": str(label),
                    primary: round(float(val), 2),
                    **({primary + "_formatted": _money(float(val))} if is_money else {}),
                }
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
        "Write a short executive report in PLAIN TEXT (no Markdown, no "
        "asterisks, no hashes, no code fences). Use exactly these four "
        "section headers on their own lines:\n\n"
        "EXECUTIVE SUMMARY\n"
        "<2-3 sentences of the headline finding>\n\n"
        "KEY METRICS\n"
        "- <metric 1>\n"
        "- <metric 2>\n"
        "- <metric 3>\n\n"
        "BREAKDOWN\n"
        "<one short paragraph per significant categorical split>\n\n"
        "RECOMMENDATION\n"
        "<2 sentences on what action to take next>\n\n"
        "For every money value, quote the *_formatted string from the "
        "aggregates verbatim (e.g. 'INR 17,70,000'). Never reformat the "
        "raw numbers yourself, and never use $ or USD. This is an Indian "
        "business. Do NOT wrap the response in ```fences```. Do NOT use "
        "** or ## anywhere. Plain text only."
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
            "narrative": "No data available to report on.",
            "sections": {"summary": "No data available to report on.",
                         "metrics": [], "breakdown": "", "recommendation": ""},
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
            sensitive=False,  # aggregates only, no raw rows in payload
        )
        clean = _strip_markdown(narrative or "")
        return {
            "narrative": clean,
            "sections": parse_sections(clean),
            "aggregates": aggregates,
            "mode": "cloud",
        }
    except Exception as e:
        logger.warning(f"[Narrative] Cloud narrative failed, falling back to local: {e}")
        try:
            local = llm_invoke(
                prompt,
                system=_NARRATIVE_SYSTEM,
                max_tokens=512,
                sensitive=True,
            )
            clean = _strip_markdown(local or "")
            return {
                "narrative": clean,
                "sections": parse_sections(clean),
                "aggregates": aggregates,
                "mode": "local-fallback",
            }
        except Exception as e2:
            logger.error(f"[Narrative] Local fallback also failed: {e2}")
            return {
                "narrative": f"Report covers {aggregates['row_count']} records across "
                             f"{aggregates['column_count']} fields.",
                "sections": {"summary": f"Report covers {aggregates['row_count']} records.",
                             "metrics": [], "breakdown": "", "recommendation": ""},
                "aggregates": aggregates,
                "mode": "static-fallback",
            }


def short_summary(query: str, df: pd.DataFrame) -> str:
    """Convenience: return just the narrative text (for PDF exec-summary block)."""
    return generate_narrative(query, df)["narrative"]
