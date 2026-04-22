"""
NexusAgent FastAPI Server — REST API + WebSocket for the React frontend.
Run: uvicorn api.server:app --reload --port 8000
"""
from __future__ import annotations

import sys
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional

# Add project root to path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File, Query, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from loguru import logger

# ── Bootstrap NexusAgent ──────────────────────────────────────────────────────
from config.settings import ensure_directories, validate_config, VERSION
ensure_directories()

# Auto-create DB if missing
from config.settings import DB_PATH
if not Path(DB_PATH).exists():
    from sql_agent.db_setup import setup_database
    setup_database()

# Auto-load sample docs
from utils.sample_docs_generator import ensure_documents_loaded
ensure_documents_loaded()

# Start monitor
try:
    from orchestrator.proactive_monitor import start_scheduler
    start_scheduler()
except Exception as e:
    logger.warning(f"Monitor start failed: {e}")

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="NexusAgent API",
    version=VERSION,
    description="Voice-first multi-agent AI — 100% local, zero API cost",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Pydantic Models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    user_id: str = "default"

class WhatIfRequest(BaseModel):
    scenario: str

class ReportRequest(BaseModel):
    query: str

class DataImportRequest(BaseModel):
    table_name: str
    if_exists: str = "fail"

class ConversationUpdate(BaseModel):
    title: str


# ═══════════════════════════════════════════════════════════════════════════════
#   HEALTH & STATUS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/health")
def health():
    from config.llm_config import health_check
    from config.settings import OLLAMA_MODEL, EMBED_MODEL, EMAIL_ENABLED, DISCORD_ENABLED
    healthy, msg = health_check(force=True)
    return {
        "status": "ok" if healthy else "degraded",
        "ollama": {"online": healthy, "message": msg, "model": OLLAMA_MODEL, "embed_model": EMBED_MODEL},
        "features": {"email": EMAIL_ENABLED, "discord": DISCORD_ENABLED},
        "version": VERSION,
    }

@app.get("/api/stats")
def system_stats():
    from rag.vector_store import get_collection_stats
    from sql_agent.schema_reader import get_table_list
    from memory.query_history import get_stats as qh_stats
    from memory.audit_logger import get_stats as audit_stats

    try:
        kb = get_collection_stats()
    except Exception:
        kb = {"document_count": 0}

    return {
        "knowledge_base": kb,
        "tables": get_table_list(),
        "query_history": qh_stats(),
        "audit": audit_stats(),
    }


# ═══════════════════════════════════════════════════════════════════════════════
#   CHAT — REST (for simple queries) + WebSocket (for streaming)
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/chat")
def chat(req: ChatRequest):
    from orchestrator.graph import run
    from memory.conversation_store import (
        create_conversation, auto_title, save_full_conversation, load_messages,
    )
    from memory.query_history import log_query

    start = time.time()

    # Ensure conversation exists
    conv_id = req.conversation_id
    if not conv_id:
        conv_id = create_conversation()
        auto_title(conv_id, req.query)

    try:
        result_state = run(req.query, user_id=req.user_id)
    except Exception as e:
        logger.error(f"Chat error: {e}")
        result_state = {
            "final_answer": f"Error processing request. Is Ollama running? Details: {e}",
            "tools_used": [],
            "citations": [],
        }

    duration_ms = int((time.time() - start) * 1000)
    answer = result_state.get("final_answer", "I couldn't generate a response.")
    tools = result_state.get("tools_used", [])

    # Build message pair
    user_msg = {
        "role": "user",
        "content": req.query,
        "tools_used": [],
        "citations": [],
        "timestamp": datetime.now().strftime("%H:%M"),
    }
    assistant_msg = {
        "role": "assistant",
        "content": answer,
        "tools_used": tools,
        "citations": result_state.get("citations", []),
        "sources_used": result_state.get("sources_used", []),
        "multi_agent": result_state.get("multi_agent", False),
        "agents_used": result_state.get("agents_used", []),
        "timestamp": datetime.now().strftime("%H:%M"),
    }

    # Save to conversation
    existing = load_messages(conv_id)
    existing.extend([user_msg, assistant_msg])
    save_full_conversation(conv_id, existing)

    # Log to query history
    try:
        log_query(
            query=req.query,
            intent=result_state.get("intent", {}).get("primary_intent", "unknown"),
            tools_used=tools,
            answer_preview=answer[:500],
            success=True,
            duration_ms=duration_ms,
            user_id=req.user_id,
        )
    except Exception:
        pass

    return {
        "conversation_id": conv_id,
        "message": assistant_msg,
        "duration_ms": duration_ms,
        "state": {
            "sql_results": _serialize_sql(result_state.get("sql_results", {})),
            "report_path": result_state.get("report_path", ""),
            "whatif_result": result_state.get("whatif_result", {}),
        },
    }


def _serialize_sql(sql_results: dict) -> dict:
    """Convert SQL results to JSON-safe format."""
    if not sql_results:
        return {}
    result = {**sql_results}
    df = result.pop("dataframe", None)
    if df is not None and hasattr(df, "to_dict"):
        result["data"] = df.head(100).to_dict(orient="records")
        result["columns"] = list(df.columns)
        result["row_count"] = len(df)
    return result


# ── WebSocket for streaming chat ──────────────────────────────────────────────
@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            query = msg.get("query", "")
            conv_id = msg.get("conversation_id")
            user_id = msg.get("user_id", "default")

            # Send "thinking" status
            await websocket.send_json({"type": "status", "status": "thinking"})

            # Run in thread pool to not block
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: _run_chat_sync(query, conv_id, user_id),
            )

            await websocket.send_json({"type": "response", **result})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")


def _run_chat_sync(query: str, conv_id: str, user_id: str) -> dict:
    """Synchronous chat runner for WebSocket."""
    req = ChatRequest(query=query, conversation_id=conv_id, user_id=user_id)
    return chat(req)


# ═══════════════════════════════════════════════════════════════════════════════
#   CONVERSATIONS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/conversations")
def list_conversations(limit: int = 20):
    from memory.conversation_store import list_conversations as lc
    return lc(limit=limit)

@app.get("/api/conversations/{conv_id}")
def get_conversation(conv_id: str):
    from memory.conversation_store import load_messages, get_conversation_info
    info = get_conversation_info(conv_id)
    if not info:
        raise HTTPException(404, "Conversation not found")
    return {"info": info, "messages": load_messages(conv_id)}

@app.patch("/api/conversations/{conv_id}")
def update_conversation(conv_id: str, body: ConversationUpdate):
    from memory.conversation_store import update_title
    update_title(conv_id, body.title)
    return {"ok": True}

@app.delete("/api/conversations/{conv_id}")
def delete_conversation(conv_id: str):
    from memory.conversation_store import delete_conversation as dc
    dc(conv_id)
    return {"ok": True}

@app.post("/api/conversations")
def create_new_conversation():
    from memory.conversation_store import create_conversation
    conv_id = create_conversation()
    return {"conversation_id": conv_id}


# ═══════════════════════════════════════════════════════════════════════════════
#   DATABASE
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/database/tables")
def list_tables():
    import sqlite3
    import pandas as pd
    from config.settings import DB_PATH

    conn = sqlite3.connect(DB_PATH)
    tables = pd.read_sql_query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", conn
    )["name"].tolist()

    result = []
    for t in tables:
        try:
            count = conn.execute(f"SELECT COUNT(*) FROM [{t}]").fetchone()[0]
        except Exception:
            count = 0
        cols = pd.read_sql_query(f"PRAGMA table_info([{t}])", conn)
        result.append({
            "name": t,
            "row_count": count,
            "column_count": len(cols),
            "is_system": t.startswith("nexus_") or t.startswith("sqlite_"),
        })
    conn.close()
    return result

@app.get("/api/database/tables/{table_name}")
def get_table_detail(table_name: str, limit: int = 50):
    import sqlite3
    import pandas as pd
    from config.settings import DB_PATH

    conn = sqlite3.connect(DB_PATH)

    # Schema
    cols = pd.read_sql_query(f"PRAGMA table_info([{table_name}])", conn)
    fks = pd.read_sql_query(f"PRAGMA foreign_key_list([{table_name}])", conn)
    row_count = conn.execute(f"SELECT COUNT(*) FROM [{table_name}]").fetchone()[0]

    # Data preview
    df = pd.read_sql_query(f"SELECT * FROM [{table_name}] LIMIT {limit}", conn)

    # Column stats for numeric columns
    stats = []
    for _, col in cols.iterrows():
        if col["type"] in ("INTEGER", "REAL", "NUMERIC"):
            try:
                s = pd.read_sql_query(
                    f"SELECT MIN([{col['name']}]) as min, MAX([{col['name']}]) as max, "
                    f"ROUND(AVG([{col['name']}]), 2) as avg FROM [{table_name}]",
                    conn,
                )
                stats.append({"column": col["name"], **s.iloc[0].to_dict()})
            except Exception:
                pass

    conn.close()

    return {
        "name": table_name,
        "row_count": row_count,
        "columns": cols.to_dict(orient="records"),
        "foreign_keys": fks.to_dict(orient="records") if not fks.empty else [],
        "data": df.to_dict(orient="records"),
        "column_stats": stats,
    }

@app.post("/api/database/import")
async def import_data(file: UploadFile = File(...), table_name: str = Query(""), if_exists: str = Query("fail")):
    import tempfile
    from sql_agent.data_import import preview_file, import_to_database

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    preview = preview_file(tmp_path)
    if preview.get("error"):
        Path(tmp_path).unlink(missing_ok=True)
        raise HTTPException(400, preview["error"])

    name = table_name or preview["suggested_table_name"]
    full_df = preview.get("_full_df")

    result = import_to_database(full_df, name, if_exists=if_exists)
    Path(tmp_path).unlink(missing_ok=True)

    if not result["success"]:
        raise HTTPException(400, result["error"])

    # Clear SQL cache
    try:
        from sql_agent.query_generator import clear_cache
        clear_cache()
    except Exception:
        pass

    return result

@app.post("/api/database/import/preview")
async def preview_import(file: UploadFile = File(...)):
    import tempfile
    from sql_agent.data_import import preview_file

    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    preview = preview_file(tmp_path, max_rows=20)
    Path(tmp_path).unlink(missing_ok=True)

    if preview.get("error"):
        raise HTTPException(400, preview["error"])

    # Remove non-serializable fields
    preview.pop("_full_df", None)
    df = preview.pop("dataframe", None)
    if df is not None:
        preview["preview_data"] = df.to_dict(orient="records")

    return preview


# ═══════════════════════════════════════════════════════════════════════════════
#   REPORTS
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/reports/generate")
def generate_report(req: ReportRequest):
    from orchestrator.graph import run
    result = run(f"Generate a report: {req.query}")
    pdf_path = result.get("report_path", "")
    if pdf_path and Path(pdf_path).exists():
        return {"path": pdf_path, "filename": Path(pdf_path).name}
    raise HTTPException(500, "Report generation failed")

@app.get("/api/reports")
def list_reports():
    from action_tools.file_dispatcher import get_recent_outputs
    return get_recent_outputs(n=20, subfolder="reports")

@app.get("/api/reports/download/{filename}")
def download_report(filename: str):
    from config.settings import REPORTS_DIR
    path = Path(REPORTS_DIR) / filename
    if not path.exists():
        raise HTTPException(404, "Report not found")
    return FileResponse(str(path), filename=filename, media_type="application/pdf")


# ═══════════════════════════════════════════════════════════════════════════════
#   WHAT-IF SIMULATOR
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/whatif")
def run_whatif(req: WhatIfRequest):
    from utils.whatif_simulator import run_full_simulation
    result = run_full_simulation(req.scenario)

    # Convert DataFrames to dicts
    for key in ("before_df", "after_df"):
        df = result.get(key)
        if df is not None and hasattr(df, "to_dict"):
            result[key] = df.to_dict(orient="records")

    return result


# ═══════════════════════════════════════════════════════════════════════════════
#   QUERY HISTORY
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/history")
def query_history(
    search: Optional[str] = None,
    intent: Optional[str] = None,
    starred: bool = False,
    limit: int = 50,
):
    from memory.query_history import get_history, get_stats
    return {
        "queries": get_history(search=search, intent_filter=intent, starred_only=starred, limit=limit),
        "stats": get_stats(),
    }

@app.post("/api/history/{query_id}/star")
def toggle_star(query_id: int):
    from memory.query_history import toggle_star as ts
    return {"starred": ts(query_id)}

@app.delete("/api/history/{query_id}")
def delete_history_entry(query_id: int):
    from memory.query_history import delete_query
    delete_query(query_id)
    return {"ok": True}

@app.delete("/api/history")
def clear_all_history():
    from memory.query_history import clear_history
    count = clear_history()
    return {"deleted": count}


# ═══════════════════════════════════════════════════════════════════════════════
#   KNOWLEDGE BASE
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/knowledge")
def knowledge_base():
    from rag.multi_document_rag import get_sources_list
    from rag.vector_store import get_collection_stats
    try:
        stats = get_collection_stats()
    except Exception:
        stats = {"document_count": 0}
    return {"sources": get_sources_list(), "stats": stats}

@app.post("/api/knowledge/upload")
async def upload_document(file: UploadFile = File(...)):
    from rag.ingestion import ingest_file
    from rag.embedder import embed_documents
    from rag.vector_store import add_documents
    from config.settings import DOCUMENTS_DIR

    dest = Path(DOCUMENTS_DIR) / file.filename
    content = await file.read()
    dest.write_bytes(content)

    docs = ingest_file(str(dest))
    if docs:
        texts = [d.page_content for d in docs]
        metas = [d.metadata for d in docs]
        embeddings = embed_documents(texts)
        added = add_documents(texts, embeddings, metas)
        return {"filename": file.filename, "chunks_added": added}
    raise HTTPException(400, "Could not process document")


# ═══════════════════════════════════════════════════════════════════════════════
#   ANOMALY MONITOR
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/monitor/status")
def monitor_status():
    from orchestrator.proactive_monitor import get_last_check_status
    return get_last_check_status()

@app.post("/api/monitor/run")
def run_monitor():
    from orchestrator.proactive_monitor import manual_trigger
    return manual_trigger()


# ═══════════════════════════════════════════════════════════════════════════════
#   EXPORT
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/export/markdown")
def export_markdown(messages: list[dict]):
    from utils.export_conversation import to_markdown
    return {"markdown": to_markdown(messages)}

@app.post("/api/export/pdf")
def export_pdf(messages: list[dict]):
    from utils.export_conversation import to_pdf
    path = to_pdf(messages)
    if path and Path(path).exists():
        return FileResponse(str(path), filename=Path(path).name, media_type="application/pdf")
    raise HTTPException(500, "PDF export failed")


# ═══════════════════════════════════════════════════════════════════════════════
#   SETTINGS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/settings")
def get_settings():
    from config.settings import (
        OLLAMA_BASE_URL, OLLAMA_MODEL, OLLAMA_FALLBACK_MODEL, EMBED_MODEL,
        EMAIL_ENABLED, DISCORD_ENABLED, MAX_SQL_RETRIES, MAX_REFLECTION_RETRIES,
        CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RETRIEVAL, VERSION,
    )
    import sys as _sys

    # Get available models
    models = []
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        if resp.status_code == 200:
            for m in resp.json().get("models", []):
                models.append({
                    "name": m.get("name", "?"),
                    "size_gb": round(m.get("size", 0) / (1024 ** 3), 1),
                    "active": OLLAMA_MODEL in m.get("name", ""),
                })
    except Exception:
        pass

    return {
        "version": VERSION,
        "python_version": _sys.version.split()[0],
        "ollama_url": OLLAMA_BASE_URL,
        "primary_model": OLLAMA_MODEL,
        "fallback_model": OLLAMA_FALLBACK_MODEL,
        "embed_model": EMBED_MODEL,
        "email_enabled": EMAIL_ENABLED,
        "discord_enabled": DISCORD_ENABLED,
        "max_sql_retries": MAX_SQL_RETRIES,
        "max_reflection_retries": MAX_REFLECTION_RETRIES,
        "chunk_size": CHUNK_SIZE,
        "chunk_overlap": CHUNK_OVERLAP,
        "top_k_retrieval": TOP_K_RETRIEVAL,
        "available_models": models,
    }

@app.post("/api/settings/reset-llm")
def reset_llm():
    from config.llm_config import reset_instances
    reset_instances()
    return {"ok": True, "message": "LLM connection reset"}

@app.post("/api/settings/clear-cache")
def clear_cache():
    from sql_agent.query_generator import clear_cache as cc
    cc()
    return {"ok": True, "message": "SQL cache cleared"}


# ═══════════════════════════════════════════════════════════════════════════════
#   WORKFLOWS
# ═══════════════════════════════════════════════════════════════════════════════
@app.get("/api/workflows")
def list_workflows():
    from workflows.storage import list_workflows as lw
    return lw()

@app.get("/api/workflows/node-types")
def get_node_types():
    from workflows.node_registry import NODE_TYPES
    return NODE_TYPES

@app.get("/api/workflows/templates")
def get_workflow_templates():
    from workflows.templates import get_all_templates
    return get_all_templates()

@app.get("/api/workflows/{wf_id}")
def get_workflow(wf_id: str):
    from workflows.storage import load_workflow
    wf = load_workflow(wf_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    return wf

@app.post("/api/workflows")
def save_workflow(wf: dict):
    from workflows.storage import save_workflow as sw
    wf_id = sw(wf)
    return {"id": wf_id}

@app.delete("/api/workflows/{wf_id}")
def delete_workflow_api(wf_id: str):
    from workflows.storage import delete_workflow
    delete_workflow(wf_id)
    return {"ok": True}

@app.post("/api/workflows/{wf_id}/toggle")
def toggle_workflow(wf_id: str, body: dict):
    from workflows.storage import toggle_enabled
    enabled = body.get("enabled", False)
    toggle_enabled(wf_id, enabled)
    try:
        from workflows.scheduler import sync_all_workflows
        sync_all_workflows()
    except Exception:
        pass
    return {"ok": True, "enabled": enabled}

@app.post("/api/workflows/{wf_id}/run")
def run_workflow(wf_id: str):
    from workflows.storage import load_workflow
    from workflows.executor import execute_workflow
    wf = load_workflow(wf_id)
    if not wf:
        raise HTTPException(404, "Workflow not found")
    result = execute_workflow(wf)
    return result

@app.post("/api/workflows/run-preview")
def run_workflow_preview(wf: dict):
    from workflows.executor import execute_workflow
    result = execute_workflow(wf)
    return result

@app.get("/api/workflows/scheduler/jobs")
def get_scheduler_jobs():
    from workflows.scheduler import get_scheduled_jobs
    return get_scheduled_jobs()

@app.get("/api/workflows/scheduler/history")
def get_workflow_history(limit: int = 30):
    from workflows.scheduler import get_run_history
    return get_run_history(limit)


# ═══════════════════════════════════════════════════════════════════════════════
#   VOICE TRANSCRIPTION
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/voice/transcribe")
async def transcribe_voice(file: UploadFile = File(...)):
    """Receive an audio file (webm/wav) and return transcribed text."""
    import tempfile
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        from voice.listener import _transcribe
        # Convert webm to wav if needed
        wav_path = tmp_path
        if suffix.lower() in (".webm", ".ogg", ".mp4", ".m4a"):
            try:
                import subprocess
                wav_path = tmp_path.replace(suffix, ".wav")
                subprocess.run(
                    ["ffmpeg", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
                    capture_output=True, timeout=10,
                )
            except Exception:
                wav_path = tmp_path  # Try raw file if ffmpeg unavailable

        text = _transcribe(wav_path)
        return {"text": text or "", "success": bool(text)}
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"text": "", "success": False, "error": str(e)}
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        wav_check = tmp_path.replace(suffix, ".wav")
        if wav_check != tmp_path:
            Path(wav_check).unlink(missing_ok=True)


# ═══════════════════════════════════════════════════════════════════════════════
#   EMAIL — MANUAL SEND APPROVAL
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/email/send")
def send_email_now(body: dict):
    """Actually send an email (after user approval in UI)."""
    from config.settings import EMAIL_ENABLED, GMAIL_USER, GMAIL_APP_PASSWORD
    if not EMAIL_ENABLED:
        raise HTTPException(400, "Email not configured. Set GMAIL_USER and GMAIL_APP_PASSWORD in .env")

    to = body.get("to", "")
    subject = body.get("subject", "")
    email_body = body.get("body", "")

    if not to or not subject or not email_body:
        raise HTTPException(400, "Missing 'to', 'subject', or 'body'")

    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        msg = MIMEMultipart()
        msg["From"] = GMAIL_USER
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(email_body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            server.send_message(msg)

        logger.success(f"[Email] Sent to {to}: {subject}")
        return {"sent": True, "to": to, "subject": subject}
    except Exception as e:
        logger.error(f"[Email] Send failed: {e}")
        raise HTTPException(500, f"Failed to send email: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
#   WEBHOOK TRIGGER
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/webhooks/{webhook_path:path}")
async def receive_webhook(webhook_path: str, request: Request):
    """Receive a webhook POST and trigger matching workflows."""
    payload = {}
    try:
        payload = await request.json()
    except Exception:
        payload = {"raw": (await request.body()).decode("utf-8", errors="replace")}

    from workflows.storage import list_workflows as lw
    from workflows.executor import execute_workflow

    target_path = f"/webhook/{webhook_path}"
    triggered = []

    for wf in lw():
        if not wf.get("enabled"):
            continue
        for node in wf.get("nodes", []):
            if node.get("type") == "webhook_trigger":
                if node.get("config", {}).get("path", "") == target_path:
                    wf["_webhook_payload"] = payload
                    result = execute_workflow(wf)
                    triggered.append({"workflow": wf["name"], "status": result.get("status")})

    if not triggered:
        raise HTTPException(404, f"No enabled workflow found for path: {target_path}")

    return {"triggered": triggered}


# ═══════════════════════════════════════════════════════════════════════════════
#   RUNTIME SETTINGS UPDATE
# ═══════════════════════════════════════════════════════════════════════════════
@app.post("/api/settings/update")
def update_runtime_setting(body: dict):
    """Update a .env setting at runtime."""
    key = body.get("key", "")
    value = body.get("value", "")
    allowed = {"DISCORD_WEBHOOK_URL", "GMAIL_USER", "GMAIL_APP_PASSWORD", "LOG_LEVEL", "ANOMALY_THRESHOLD"}

    if key not in allowed:
        raise HTTPException(400, f"Cannot update '{key}'. Allowed: {', '.join(allowed)}")

    env_path = ROOT / ".env"
    lines = env_path.read_text(encoding="utf-8").splitlines() if env_path.exists() else []

    updated = False
    for i, line in enumerate(lines):
        if line.startswith(f"{key}="):
            lines[i] = f"{key}={value}"
            updated = True
            break
    if not updated:
        lines.append(f"{key}={value}")

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # Reload into os.environ
    import os
    os.environ[key] = value

    return {"ok": True, "key": key}


# ═══════════════════════════════════════════════════════════════════════════════
#   SERVE REACT FRONTEND (production only — when dist/ exists)
# ═══════════════════════════════════════════════════════════════════════════════
_frontend_dist = ROOT / "frontend" / "dist"
if _frontend_dist.is_dir():
    # Serve index.html for all non-API routes (SPA fallback)
    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        file_path = _frontend_dist / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_frontend_dist / "index.html"))

    app.mount("/assets", StaticFiles(directory=str(_frontend_dist / "assets")), name="static")
