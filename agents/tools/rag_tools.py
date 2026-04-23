"""RAG + SQL tools — let the agent query the knowledge base and data warehouse."""
from __future__ import annotations

from agents.tool_registry import register_tool


def _search_knowledge(ctx, args):
    from rag.retriever import retrieve
    results = retrieve(args["query"], top_k=int(args.get("top_k", 5)))
    return [
        {
            "source": r.get("source", ""),
            "text": (r.get("text") or r.get("page_content", ""))[:1000],
            "score": r.get("score"),
        }
        for r in (results or [])
    ]


register_tool(
    name="search_knowledge",
    description=(
        "Search the uploaded document knowledge base using semantic search. "
        "Returns the top-k most relevant chunks with their source. Use for "
        "company policy, uploaded PDFs, reference documents."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {"type": "string"},
            "top_k": {"type": "integer", "default": 5},
        },
        "required": ["query"],
    },
    handler=_search_knowledge,
)


def _run_business_query(ctx, args):
    """
    Run a natural-language question against the data warehouse (SQLite).
    Uses the existing NL→SQL pipeline; results are capped by SQL_MAX_ROWS.
    """
    from sql_agent.executor import execute_query
    question = args["question"]
    result = execute_query(question, log_to_audit=True)
    df = result.get("dataframe")
    rows = df.to_dict(orient="records") if df is not None and len(df) else []
    return {
        "success": result.get("success", False),
        "explanation": result.get("explanation", ""),
        "query_used": result.get("query_used", ""),
        "row_count": len(rows),
        "rows": rows[:200],  # cap what we send back to the LLM
    }


def _research(ctx, args):
    from agents.research_agent import research
    return research(
        subject=args["subject"],
        context=args.get("context", ""),
        save_as_interaction=bool(args.get("save_as_interaction", False)),
        business_id=ctx["business_id"],
        user_id=ctx["user_id"],
        contact_id=args.get("contact_id"),
        company_id=args.get("company_id"),
        deal_id=args.get("deal_id"),
    )


register_tool(
    name="research_subject",
    description=(
        "Research a company, person, or topic on the public web and return "
        "a business-relevant brief. Optionally save the brief as a CRM "
        "interaction attached to a contact/company/deal."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "subject": {"type": "string", "description": "Company name, person, or topic"},
            "context": {"type": "string", "description": "Extra context from the user"},
            "save_as_interaction": {"type": "boolean", "default": False},
            "contact_id": {"type": "string"},
            "company_id": {"type": "string"},
            "deal_id": {"type": "string"},
        },
        "required": ["subject"],
    },
    handler=_research,
)


register_tool(
    name="run_business_query",
    description=(
        "Ask a question in plain English about the data in the warehouse — sales, "
        "revenue, customer metrics, etc. The system generates SQL, runs it, and "
        "returns both the data and a plain-English explanation. Use for "
        "data-driven questions, never for CRM/tasks/invoices (those have their "
        "own tools)."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string"},
        },
        "required": ["question"],
    },
    handler=_run_business_query,
)
