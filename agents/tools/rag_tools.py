"""RAG + SQL tools — let the agent query the knowledge base and data warehouse."""
from __future__ import annotations

from loguru import logger

from agents.tool_registry import register_tool


def _search_knowledge(ctx, args):
    """retrieve() returns a dict {results, low_confidence, warning, query}.
    Earlier this function iterated the dict directly — iterating yields
    keys (strings), so r.get(...) blew up with 'str' has no attribute
    'get'. Unwrap properly and surface the warning when present.

    Optional `category` filter narrows the search to documents tagged with
    that category (competitor / internal / client / contract / social /
    other). The filter is applied post-retrieval against the nexus_documents
    table so we don't have to rebuild the vector index per category.
    """
    from rag.retriever import retrieve
    category = (args.get("category") or "").strip().lower() or None
    resp = retrieve(args["query"], top_k=int(args.get("top_k", 5)))
    if not isinstance(resp, dict):
        return {"results": [], "warning": "Retriever returned unexpected shape"}
    items = resp.get("results") or []

    # If a category was requested, fetch the matching doc paths for this
    # business and keep only chunks whose source matches one of them.
    allowed_sources = None
    if category:
        try:
            from config.db import get_conn
            import sqlite3 as _sq
            conn = get_conn()
            conn.row_factory = _sq.Row
            try:
                rows = conn.execute(
                    "SELECT file_path FROM nexus_documents "
                    "WHERE business_id = ? AND category = ?",
                    (ctx.get("business_id", ""), category),
                ).fetchall()
            finally:
                conn.close()
            allowed_sources = {(r["file_path"] or "") for r in rows}
        except Exception as e:
            logger.warning(f"[search_knowledge] category filter failed: {e}")
            allowed_sources = None

    def _src(r):
        return (r.get("source") if isinstance(r, dict) else "") or ""

    if allowed_sources is not None:
        # Keep chunks whose source path either matches exactly or appears
        # in any of the allowed paths (Chroma may store stem-only).
        items = [r for r in items if _src(r) and any(_src(r) in p or p in _src(r) for p in allowed_sources)]

    out_results = [
        {
            "source": _src(r),
            "page":   (r.get("page")   if isinstance(r, dict) else "") or "",
            "text":   ((r.get("text") if isinstance(r, dict) else "") or
                       (r.get("page_content") if isinstance(r, dict) else "") or "")[:1000],
            "confidence": (r.get("confidence") if isinstance(r, dict) else None),
        }
        for r in items
    ]
    out = {
        "results": out_results,
        "low_confidence": bool(resp.get("low_confidence")),
        "warning": resp.get("warning"),
        "query": resp.get("query") or args.get("query"),
    }
    if category is not None:
        out["category_filter"] = category
        if allowed_sources is not None and len(allowed_sources) == 0:
            out["warning"] = (
                f"No documents categorised as '{category}' in this workspace. "
                f"Upload a doc and set its category in /documents to enable this search."
            )
    return out


register_tool(
    name="search_knowledge",
    description=(
        "Search the uploaded document knowledge base using semantic search. "
        "Returns the top-k most relevant chunks with their source. Use for "
        "company policy, uploaded PDFs, reference documents. "
        "Pass `category` to restrict the search to one bucket "
        "(competitor / internal / client / contract / social / other) — "
        "essential when comparing 'our docs' vs 'their docs'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query":    {"type": "string"},
            "top_k":    {"type": "integer", "default": 5},
            "category": {
                "type": "string",
                "description": "Restrict to docs tagged with this category. Omit for all categories.",
                "enum": ["competitor", "internal", "client", "contract", "social", "other"],
            },
        },
        "required": ["query"],
    },
    handler=_search_knowledge,
)


def _generate_data_report(ctx, args):
    """
    Run a natural-language business question against the data warehouse and
    render the result into downloadable file(s). Returns the data explanation
    plus file paths so the UI / WhatsApp bridge can attach them.
    """
    from sql_agent.executor import execute_query
    from pathlib import Path
    from datetime import datetime

    question = args["question"]
    title = (args.get("title") or question[:60]).strip() or "Business Report"
    formats = args.get("formats") or ["pdf"]
    if isinstance(formats, str):
        formats = [f.strip().lower() for f in formats.split(",") if f.strip()]
    formats = [f for f in formats if f in ("pdf", "xlsx", "csv")] or ["pdf"]

    # Step 1: run the query
    result = execute_query(question, log_to_audit=True)
    df = result.get("dataframe")
    if df is None or df.empty:
        return {
            "success": False,
            "explanation": result.get("explanation", "Query returned no data."),
            "query_used": result.get("query_used", ""),
            "files": [],
        }

    attachments = []

    # Step 2: PDF (with auto-generated chart if numeric columns exist)
    if "pdf" in formats:
        try:
            from report_generator.pdf_builder import build_pdf
            from report_generator.chart_builder import build_chart
            chart_path = None
            try:
                chart_path = build_chart(df, title=title)
            except Exception:
                chart_path = None
            insights = []
            explanation = result.get("explanation", "")
            for line in explanation.split(". "):
                line = line.strip()
                if line and len(insights) < 4:
                    insights.append(line.rstrip("."))
            pdf_path = build_pdf(
                title=title,
                executive_summary=explanation or f"Report for: {question}",
                dataframe=df,
                chart_image_path=chart_path,
                key_insights=insights,
                subtitle=f"Generated {datetime.now().strftime('%b %d, %Y at %H:%M')}",
            )
            attachments.append({
                "path": str(pdf_path),
                "filename": Path(pdf_path).name,
                "mime_type": "application/pdf",
            })
        except Exception as e:
            logger.warning(f"[generate_data_report] PDF failed: {e}")

    # Step 3: Excel
    if "xlsx" in formats:
        try:
            from config.settings import REPORTS_DIR
            Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40].strip() or "report"
            xlsx_path = Path(REPORTS_DIR) / f"report_{safe_title}_{stamp}.xlsx"
            df.to_excel(str(xlsx_path), index=False, sheet_name="Data")
            attachments.append({
                "path": str(xlsx_path),
                "filename": xlsx_path.name,
                "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            })
        except Exception as e:
            logger.warning(f"[generate_data_report] XLSX failed: {e}")

    # Step 4: CSV
    if "csv" in formats:
        try:
            from config.settings import REPORTS_DIR
            Path(REPORTS_DIR).mkdir(parents=True, exist_ok=True)
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_title = "".join(c for c in title if c.isalnum() or c in " _-")[:40].strip() or "report"
            csv_path = Path(REPORTS_DIR) / f"report_{safe_title}_{stamp}.csv"
            df.to_csv(str(csv_path), index=False)
            attachments.append({
                "path": str(csv_path),
                "filename": csv_path.name,
                "mime_type": "text/csv",
            })
        except Exception as e:
            logger.warning(f"[generate_data_report] CSV failed: {e}")

    return {
        "success": True,
        "explanation": result.get("explanation", ""),
        "query_used": result.get("query_used", ""),
        "row_count": len(df),
        "preview_rows": df.head(20).to_dict(orient="records"),
        "files": attachments,
    }


register_tool(
    name="generate_data_report",
    description=(
        "Run a business data question AND produce a downloadable report file. "
        "Use this whenever the user asks for a 'report', 'list', or 'export' "
        "of data and wants a file (PDF, Excel, or CSV). The PDF includes an "
        "auto-generated chart + table + executive summary. Call this instead "
        "of run_business_query when the user mentions 'file', 'download', "
        "'PDF', 'Excel', 'CSV', or 'report'."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "question": {"type": "string", "description": "Natural-language business question"},
            "title": {"type": "string", "description": "Short report title (optional)"},
            "formats": {
                "type": "array",
                "items": {"type": "string", "enum": ["pdf", "xlsx", "csv"]},
                "description": "Output formats, default ['pdf']",
            },
        },
        "required": ["question"],
    },
    handler=_generate_data_report,
    summary_fn=lambda a: f"Report: {a.get('title') or a.get('question', '')[:60]} → {'+'.join(a.get('formats') or ['pdf'])}",
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
