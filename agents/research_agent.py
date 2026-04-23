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
