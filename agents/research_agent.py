"""
Research agent — given a subject (company, person, topic), does a web lookup,
summarizes into a business-relevant brief, and optionally saves the result as
a CRM interaction so you have a record of what the agent found.

Privacy note:
- Only performs public web searches. Never exfiltrates your business data.
- If the LLM is Claude, your subject string is sent to Anthropic's API (the
  web search happens via DuckDuckGo regardless of LLM).
- If running on local Ollama, nothing business-sensitive leaves the machine
  besides the subject string (which goes to DuckDuckGo for the search).
"""
from __future__ import annotations

from typing import Dict, Any, Optional

from loguru import logger

from config.llm_provider import invoke as llm_invoke


def _web_search(query: str, max_results: int = 6) -> str:
    """Reuses the same DuckDuckGo path the workflow web_search node uses."""
    import urllib.request
    import urllib.parse
    import json as _json

    try:
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "NexusAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read().decode())
    except Exception as e:
        return f"(web search unavailable: {e})"

    snippets = []
    abstract = data.get("AbstractText") or data.get("Abstract")
    if abstract:
        snippets.append(abstract)
    for r in data.get("RelatedTopics", [])[:max_results]:
        if isinstance(r, dict):
            if "Text" in r:
                snippets.append(r["Text"])
            elif "Topics" in r:
                for sub in r["Topics"][:2]:
                    if "Text" in sub:
                        snippets.append(sub["Text"])
    if not snippets:
        return f"(no public information found for '{query}')"
    return "\n\n".join(snippets[:max_results])


_BRIEF_PROMPT = """You are preparing a briefing on "{subject}" for a business meeting.

Here is what a web search turned up:
---
{findings}
---

Write a concise, actionable business brief. Structure:
1) One-sentence summary of what/who this is.
2) 2-4 bullet points of the most relevant facts (industry, size if company, notable news).
3) 2-3 suggested talking points or questions for the user to raise.

If the findings are sparse or unreliable, say so honestly in a single sentence \
and stop. Do NOT make things up. Keep the total under 180 words."""


def research(subject: str, context: str = "", save_as_interaction: bool = False,
             business_id: Optional[str] = None, user_id: Optional[str] = None,
             contact_id: Optional[str] = None, company_id: Optional[str] = None,
             deal_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the research pipeline and return a brief.

    If save_as_interaction=True and any of contact_id/company_id/deal_id is
    set, the brief is logged as a CRM interaction so the user has a record.
    """
    subject = (subject or "").strip()
    if not subject:
        raise ValueError("subject is required")
    if len(subject) > 200:
        raise ValueError("subject too long")

    findings = _web_search(subject)
    prompt = _BRIEF_PROMPT.format(subject=subject, findings=findings[:4000])
    if context:
        prompt = f"Additional context from the user: {context[:600]}\n\n" + prompt

    try:
        brief = llm_invoke(prompt, system="You write crisp business briefs.", max_tokens=600, temperature=0.2)
    except Exception as e:
        logger.warning(f"[Research] LLM failed: {e}")
        brief = f"Research findings for {subject}:\n\n{findings}"

    result = {
        "subject": subject,
        "brief": brief.strip(),
        "raw_findings": findings[:3000],
    }

    if save_as_interaction and business_id and user_id and (contact_id or company_id or deal_id):
        try:
            from api import crm as _crm
            interaction = _crm.create_interaction(business_id, user_id, {
                "type": "note",
                "subject": f"Research: {subject}"[:200],
                "summary": brief[:3900],
                "contact_id": contact_id,
                "company_id": company_id,
                "deal_id": deal_id,
            })
            result["interaction_id"] = interaction["id"]
        except Exception as e:
            logger.warning(f"[Research] Could not save interaction: {e}")
            result["interaction_error"] = str(e)

    return result


# ── Structured research reports ─────────────────────────────────────────────
def structured_research(subject: str, context: str = "") -> Dict[str, Any]:
    """
    Research wrapper that returns a structured report instead of free text.

    Shape:
        {
          subject:     str,
          summary:     str       — one-sentence executive summary
          findings:    [         — 3-5 bullet points
             {title, detail}
          ],
          sources:     [str]     — short labels for where info came from
          next_steps:  [str]     — 2-3 suggested actions for the user
          raw:         str       — original brief for fallback display
        }

    The LLM is asked to return pipe-separated fields so parsing is robust
    without requiring tool-use. Falls back to the raw brief if parsing fails.
    """
    base = research(subject, context)
    brief = base.get("brief", "") or ""
    raw_findings = base.get("raw_findings", "") or ""

    schema_prompt = (
        f"You previously wrote this brief about '{subject}':\n\n{brief[:1500]}\n\n"
        f"Raw findings: {raw_findings[:1500]}\n\n"
        "Re-output the brief as structured fields, one per line:\n"
        "SUMMARY: <one sentence>\n"
        "FINDING: <title> || <detail>\n"
        "FINDING: <title> || <detail>\n"
        "FINDING: <title> || <detail>\n"
        "SOURCE: <short label>\n"
        "NEXT: <suggested action>\n"
        "NEXT: <suggested action>\n\n"
        "Each FINDING must have a title and detail separated by ' || '. "
        "Do NOT include any other text, explanations, or headings."
    )
    try:
        text = llm_invoke(schema_prompt,
                          system="You output structured reports. No extra text.",
                          max_tokens=700, temperature=0.1)
    except Exception as e:
        logger.warning(f"[Research] structured re-parse failed: {e}")
        text = ""

    summary, findings, sources, next_steps = _parse_structured(text or brief)
    # If parsing produced nothing, fall back to using brief as summary.
    if not summary:
        summary = (brief.split("\n", 1)[0] or brief)[:220]

    return {
        "subject":    subject,
        "summary":    summary,
        "findings":   findings,
        "sources":    sources,
        "next_steps": next_steps,
        "raw":        brief,
    }


def _parse_structured(text: str):
    """Parse the pipe-separated schema into lists. Tolerant of minor format drift."""
    summary = ""
    findings: list = []
    sources: list = []
    next_steps: list = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        upper = line.upper()
        if upper.startswith("SUMMARY:"):
            summary = line.split(":", 1)[1].strip()
        elif upper.startswith("FINDING:"):
            body = line.split(":", 1)[1].strip()
            if "||" in body:
                title, detail = body.split("||", 1)
                findings.append({"title": title.strip(), "detail": detail.strip()})
            else:
                findings.append({"title": body[:80], "detail": ""})
        elif upper.startswith("SOURCE:"):
            sources.append(line.split(":", 1)[1].strip())
        elif upper.startswith("NEXT:"):
            next_steps.append(line.split(":", 1)[1].strip())
    return summary, findings, sources, next_steps


def save_report_to_kb(business_id: str, report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write a structured research report into the RAG knowledge base so future
    queries can cite it. Returns {document_id, chunks_added}.

    The vector store keeps its own copy; we also log a `nexus_documents` row
    so it shows on the Documents page.
    """
    from rag import vector_store
    import uuid as _uuid
    import json as _json
    import sqlite3 as _sq
    from config.settings import DB_PATH

    subject = (report.get("subject") or "Research").strip()[:200]
    body_parts = [f"# Research: {subject}", ""]
    if report.get("summary"):
        body_parts += ["## Summary", report["summary"], ""]
    if report.get("findings"):
        body_parts += ["## Findings"]
        for f in report["findings"]:
            body_parts.append(f"- **{f.get('title','')}** — {f.get('detail','')}")
        body_parts.append("")
    if report.get("sources"):
        body_parts += ["## Sources"] + [f"- {s}" for s in report["sources"]] + [""]
    if report.get("next_steps"):
        body_parts += ["## Next steps"] + [f"- {s}" for s in report["next_steps"]] + [""]
    body = "\n".join(body_parts)

    doc_id = f"research-{_uuid.uuid4().hex[:10]}"
    added = vector_store.add_documents(
        texts=[body],
        metadatas=[{"business_id": business_id, "source": "research",
                    "title": f"Research: {subject}"}],
        ids=[doc_id],
    )

    try:
        conn = _sq.connect(DB_PATH)
        conn.execute(
            "INSERT INTO nexus_documents "
            "(id, business_id, template_key, title, format, file_path, "
            " variables, created_at, created_by) "
            "VALUES (?, ?, 'research_report', ?, 'md', '', ?, ?, 'system')",
            (doc_id, business_id, f"Research: {subject}",
             _json.dumps({"subject": subject}), __import__("datetime").now_iso()),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"[Research] save_report_to_kb: document row write failed: {e}")

    return {"document_id": doc_id, "chunks_added": added or 1}
