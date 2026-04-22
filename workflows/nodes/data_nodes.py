"""
Data node implementations — SQL, RAG, Web Search, Transform.
"""
from __future__ import annotations
from typing import Dict, Any
from loguru import logger


def run_sql_query(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    mode = config.get("mode", "natural_language")
    max_rows = config.get("max_rows", 100)

    try:
        from sql_agent.executor import execute_query
        from sql_agent.query_generator import generate_sql

        if mode == "raw_sql":
            sql = config.get("sql", "SELECT 1")
            result = execute_query("custom SQL", sql=sql)
        else:
            question = config.get("question", "Show all data")
            result = execute_query(question)

        if result["success"]:
            df = result["dataframe"]
            if len(df) > max_rows:
                df = df.head(max_rows)
            ctx["_last_df"] = df
            ctx["_last_df_summary"] = df.iloc[0].to_dict() if not df.empty else {}
            ctx["output"] = result.get("explanation", f"{len(df)} rows returned")
            ctx["_df_text"] = df.to_string(index=False)[:3000]
            logger.info(f"[DataNode] sql_query → {len(df)} rows")
        else:
            ctx["output"] = f"SQL failed: {result.get('error')}"
    except Exception as e:
        ctx["output"] = f"SQL error: {e}"
        logger.error(f"[DataNode] sql_query error: {e}")

    return ctx


def run_rag_search(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    query_template = config.get("query", "What is our policy?")
    top_k = config.get("top_k", 3)

    # Replace {input} with previous output
    prev_output = str(ctx.get("output", ""))
    query = query_template.replace("{input}", prev_output[:500])

    try:
        from rag.retriever import retrieve
        result = retrieve(query, top_k=top_k)
        results = result.get("results", [])
        if results:
            texts = "\n\n".join(
                f"[{r['source']} p.{r['page']}] {r['text'][:400]}"
                for r in results
            )
            ctx["output"] = texts
            ctx["_rag_results"] = results
        else:
            ctx["output"] = result.get("warning", "No documents found.")
        logger.info(f"[DataNode] rag_search → {len(results)} results")
    except Exception as e:
        ctx["output"] = f"RAG error: {e}"

    return ctx


def run_web_search(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    query_template = config.get("query", "latest news")
    max_results = config.get("max_results", 5)
    prev_output = str(ctx.get("output", ""))
    query = query_template.replace("{input}", prev_output[:200])

    results_text = ""
    try:
        import urllib.request, urllib.parse, json as _json
        encoded = urllib.parse.quote(query)
        url = f"https://api.duckduckgo.com/?q={encoded}&format=json&no_html=1&skip_disambig=1"
        req = urllib.request.Request(url, headers={"User-Agent": "NexusAgent/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = _json.loads(resp.read().decode())

        related = data.get("RelatedTopics", [])[:max_results]
        snippets = []
        for r in related:
            if "Text" in r:
                snippets.append(r["Text"])
            elif "Topics" in r:
                for sub in r["Topics"][:2]:
                    if "Text" in sub:
                        snippets.append(sub["Text"])

        if snippets:
            results_text = f"Web search results for '{query}':\n\n" + "\n\n".join(snippets[:max_results])
        else:
            results_text = f"No web results found for '{query}'"

    except Exception as e:
        results_text = f"Web search unavailable: {e}"

    ctx["output"] = results_text
    logger.info(f"[DataNode] web_search → {len(results_text)} chars")
    return ctx


def run_data_transform(config: Dict[str, Any], ctx: Dict[str, Any]) -> Dict[str, Any]:
    operation = config.get("operation", "top_n")
    df = ctx.get("_last_df")

    try:
        import pandas as pd

        if df is None or (hasattr(df, "empty") and df.empty):
            ctx["output"] = "No data to transform"
            return ctx

        col = config.get("column", df.select_dtypes(include="number").columns[0] if not df.empty else "")

        if operation == "top_n":
            n = config.get("n", 5)
            if col in df.columns:
                df = df.nlargest(n, col)
            else:
                df = df.head(n)
            ctx["_last_df"] = df
            ctx["output"] = f"Top {n} rows:\n{df.to_string(index=False)}"

        elif operation == "sort":
            if col in df.columns:
                df = df.sort_values(col, ascending=False)
            ctx["_last_df"] = df
            ctx["output"] = df.to_string(index=False)

        elif operation == "sum_column":
            if col in df.columns:
                total = df[col].sum()
                ctx["output"] = f"Sum of {col}: {total:,.2f}"
            else:
                ctx["output"] = f"Column '{col}' not found"

        elif operation == "format_text":
            template = config.get("text_template", "{row}")
            lines = []
            for _, row in df.iterrows():
                try:
                    line = template
                    for c in df.columns:
                        line = line.replace(f"{{row.{c}}}", str(row[c]))
                    lines.append(line)
                except Exception:
                    lines.append(str(row.to_dict()))
            ctx["output"] = "\n".join(lines[:50])

    except Exception as e:
        ctx["output"] = f"Transform error: {e}"

    return ctx
