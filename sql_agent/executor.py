"""
SQL Executor — runs SQL queries with self-correction on error.
Returns DataFrame + plain-English explanation.
Includes smarter retry logic with distinct error tracking.
"""
from __future__ import annotations

import time
import sqlite3
from pathlib import Path
from typing import Dict, Any

import pandas as pd
from loguru import logger

from config.settings import DB_PATH, MAX_SQL_RETRIES, SQL_QUERY_TIMEOUT_SECONDS, SQL_MAX_ROWS
from config.llm_provider import invoke as llm_invoke
from sql_agent.schema_reader import get_schema_string
from sql_agent.query_generator import generate_sql, _validate_sql


class QueryTimeout(Exception):
    """Raised when a SQL query exceeds SQL_QUERY_TIMEOUT_SECONDS."""


def _install_timeout(conn: sqlite3.Connection, deadline: float) -> None:
    """
    Install a SQLite progress handler that raises QueryTimeout when wall-clock
    time exceeds `deadline`. The callback runs every N VM steps; returning
    non-zero cancels the query.
    """
    def _check():
        if time.time() > deadline:
            return 1  # non-zero → interrupt
        return 0
    # Check every 1000 VM ops — low overhead, responsive cancellation
    conn.set_progress_handler(_check, 1000)


def _fix_sql_with_llm(original_question: str, broken_sql: str,
                       error_msg: str, schema: str, previous_errors: list[str] = None) -> str:
    """Ask LLM to fix a broken SQL query, aware of previous failed attempts."""

    history_hint = ""
    if previous_errors:
        history_hint = (
            "\nPREVIOUS FAILED ATTEMPTS AND ERRORS:\n"
            + "\n".join(f"- {e}" for e in previous_errors[-3:])
            + "\nDo NOT repeat the same mistakes.\n"
        )

    prompt = f"""The following SQLite query failed with an error. Fix it.

SCHEMA:
{schema}

ORIGINAL QUESTION: {original_question}

BROKEN SQL:
{broken_sql}

ERROR MESSAGE:
{error_msg}
{history_hint}
RULES:
- Fix ONLY the SQL error. Do not change the intent of the query.
- Make sure all table and column names exist in the schema above.
- Use proper SQLite syntax (e.g., strftime for dates, || for string concatenation).
- Write ONLY the corrected SQL query wrapped in ```sql ... ``` fences. No explanations."""

    try:
        response = llm_invoke(prompt, max_tokens=512)
        from sql_agent.query_generator import _extract_sql
        return _extract_sql(response)
    except Exception as e:
        logger.error(f"[Executor] SQL fix LLM call failed: {e}")
        return ""


def _explain_result(question: str, df: pd.DataFrame, intent_type: str) -> str:
    """Ask LLM to explain the query result in plain English."""
    if df.empty:
        return "The query returned no results matching your criteria."

    sample = df.head(10).to_string(index=False)
    shape = f"{len(df)} rows x {len(df.columns)} columns"

    prompt = f"""Answer this business question using the data below. Use specific numbers. Format money with $ and commas. 2-3 sentences.

Question: {question}
Data ({shape}):
{sample}"""

    try:
        response = llm_invoke(prompt, max_tokens=256)
        return response.strip()
    except Exception as e:
        logger.warning(f"[Executor] Explanation LLM call failed: {e}")
        if not df.empty:
            top = df.iloc[0].to_dict()
            return f"Query returned {len(df)} rows. First result: {top}"
        return f"Query returned {len(df)} rows."


def execute_query(
    question: str,
    sql: str = None,
    intent_type: str = "mixed",
    log_to_audit: bool = True,
) -> Dict[str, Any]:
    """
    Execute a SQL query against the local database.
    If SQL is not provided, generates it from the question.
    Self-corrects on error up to MAX_SQL_RETRIES times with error history tracking.

    Returns:
        {dataframe, explanation, query_used, retries_needed, intent_type, success, error}
    """
    if not Path(DB_PATH).exists():
        logger.warning("[Executor] DB missing — running setup.")
        from sql_agent.db_setup import setup_database
        setup_database()

    schema = get_schema_string()

    # Generate SQL if not provided
    if not sql:
        gen = generate_sql(question, schema)
        sql = gen.get("sql", "")
        intent_type = gen.get("intent_type", intent_type)
        if gen.get("error") or not sql:
            return {
                "dataframe": pd.DataFrame(),
                "explanation": f"Could not generate a query for your question: {gen.get('error', 'unknown error')}",
                "query_used": "",
                "retries_needed": 0,
                "intent_type": intent_type,
                "success": False,
                "error": gen.get("error"),
            }

    retries = 0
    last_error = None
    query_used = sql
    start_time = time.time()
    error_history: list[str] = []  # Track distinct errors to avoid loops

    while retries <= MAX_SQL_RETRIES:
        conn = None
        try:
            conn = sqlite3.connect(DB_PATH)
            deadline = time.time() + SQL_QUERY_TIMEOUT_SECONDS
            _install_timeout(conn, deadline)
            # Enforce a hard row cap so a pathological query doesn't exhaust memory.
            # We wrap the user's query in a subquery; only applied to SELECTs.
            capped_sql = query_used
            if SQL_MAX_ROWS > 0 and capped_sql.strip().lower().startswith("select"):
                # Use a LIMIT on top; if the query already has LIMIT it will still be respected as an outer bound.
                capped_sql = f"SELECT * FROM ({query_used}) AS _capped LIMIT {SQL_MAX_ROWS + 1}"
            try:
                df = pd.read_sql_query(capped_sql, conn)
            except sqlite3.OperationalError as oe:
                if "interrupted" in str(oe).lower():
                    raise QueryTimeout(f"Query exceeded {SQL_QUERY_TIMEOUT_SECONDS}s timeout")
                raise
            finally:
                if conn is not None:
                    conn.close()
            truncated = len(df) > SQL_MAX_ROWS
            if truncated:
                df = df.head(SQL_MAX_ROWS)

            duration_ms = int((time.time() - start_time) * 1000)
            explanation = _explain_result(question, df, intent_type)
            if truncated:
                explanation = (
                    f"[Showing first {SQL_MAX_ROWS} rows — query result was larger.]\n\n"
                    + explanation
                )

            logger.success(
                f"[Executor] '{question[:50]}' -> {len(df)} rows in {duration_ms}ms "
                f"(retries: {retries}{', TRUNCATED' if truncated else ''})"
            )

            if log_to_audit:
                try:
                    from memory.audit_logger import log_tool_call
                    log_tool_call(
                        tool="sql_executor",
                        input_summary=f"Q: {question[:100]}",
                        output_summary=f"{len(df)} rows returned",
                        duration_ms=duration_ms,
                        approved=True,
                        success=True,
                    )
                except Exception:
                    pass

            return {
                "dataframe": df,
                "explanation": explanation,
                "query_used": query_used,
                "retries_needed": retries,
                "intent_type": intent_type,
                "success": True,
                "error": None,
            }

        except Exception as e:
            last_error = str(e)
            error_history.append(f"SQL: {query_used[:100]} | Error: {last_error[:100]}")
            logger.warning(
                f"[Executor] Attempt {retries+1} failed: {last_error[:100]}"
            )

            # Check if we're seeing the same error repeatedly
            if retries > 0 and len(error_history) >= 2:
                if error_history[-1] == error_history[-2]:
                    logger.warning("[Executor] Same error repeated — stopping retry loop.")
                    break

            if retries < MAX_SQL_RETRIES:
                fixed_sql = _fix_sql_with_llm(
                    question, query_used, last_error, schema,
                    previous_errors=error_history,
                )
                if fixed_sql and _validate_sql(fixed_sql) and fixed_sql != query_used:
                    query_used = fixed_sql
                    logger.info("[Executor] Retrying with fixed SQL...")
                else:
                    logger.warning("[Executor] LLM fix produced invalid or identical SQL. Stopping.")
                    break
            retries += 1

    # All retries exhausted
    duration_ms = int((time.time() - start_time) * 1000)
    if log_to_audit:
        try:
            from memory.audit_logger import log_tool_call
            log_tool_call(
                tool="sql_executor",
                input_summary=f"Q: {question[:100]}",
                output_summary="FAILED",
                duration_ms=duration_ms,
                approved=True,
                success=False,
                error=last_error,
            )
        except Exception:
            pass

    # Provide a helpful error message
    error_hint = ""
    if last_error:
        if "no such table" in last_error.lower():
            error_hint = " The query referenced a table that doesn't exist in the database."
        elif "no such column" in last_error.lower():
            error_hint = " The query referenced a column that doesn't exist."
        elif "syntax error" in last_error.lower():
            error_hint = " The generated SQL had a syntax error."

    return {
        "dataframe": pd.DataFrame(),
        "explanation": (
            f"I couldn't execute this query after {retries} attempts.{error_hint} "
            f"Try rephrasing your question with more specific terms."
        ),
        "query_used": query_used,
        "retries_needed": retries,
        "intent_type": intent_type,
        "success": False,
        "error": last_error,
    }
