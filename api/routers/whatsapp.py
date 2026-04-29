"""
WhatsApp link flow + bridge webhook.

Per-user link: the user generates a 6-char code, texts it to the bot,
and the local Node bridge calls back here to attach their phone number
to their account. Inbound messages and attachment fetches both come
from the bridge protected by `X-Nexus-Secret`.
"""
from __future__ import annotations

import asyncio
import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from loguru import logger

from api.auth import get_current_context, get_current_user
from api import whatsapp as _wa

router = APIRouter(tags=["whatsapp"])

# Hard cap on uploaded media — keeps a malicious / accidental huge upload
# from blowing memory. WhatsApp's own audio/document limit is 16-100 MB
# depending on type; 25 MB matches what the existing voice endpoint enforces.
_MAX_MEDIA_BYTES = 25 * 1024 * 1024


_UNLINKED_PROMPT = {
    "text": (
        "Hi 👋 — this number isn't linked to a NexusAgent account.\n\n"
        "Open NexusAgent in your browser, go to *Settings → WhatsApp*, "
        "click *Generate link code*, then text the 6-character code back here."
    ),
    "attachments": [],
}


def _resolve_phone(phone: str) -> tuple[str, dict | None]:
    """Normalize a phone, look up its linked account. Returns (phone, account|None)."""
    phone_norm = _wa._normalize_phone(phone)
    if not phone_norm:
        raise HTTPException(400, "Missing or invalid phone number")
    return phone_norm, _wa._get_account_by_phone(phone_norm)


def _ffmpeg_to_wav(in_path: str, in_suffix: str) -> str:
    """Convert browser/WA-recorded audio to 16kHz mono WAV. Returns the path
    that should be transcribed (the original if conversion isn't available)."""
    if in_suffix.lower() not in (".webm", ".ogg", ".oga", ".mp4", ".m4a", ".opus"):
        return in_path
    try:
        wav_path = in_path.rsplit(".", 1)[0] + ".wav"
        subprocess.run(
            ["ffmpeg", "-i", in_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
            capture_output=True, timeout=15,
        )
        return wav_path if Path(wav_path).exists() else in_path
    except Exception as e:
        logger.warning(f"[WhatsApp] ffmpeg conversion skipped: {e}")
        return in_path


@router.post("/api/whatsapp/link/generate")
def whatsapp_generate_link(ctx: dict = Depends(get_current_context)):
    """Issue a 6-char code the user will text to the WhatsApp bot to link their phone."""
    return _wa.generate_link_token(ctx["user"]["id"], ctx["business_id"])


@router.get("/api/whatsapp/account")
def whatsapp_account(ctx: dict = Depends(get_current_context)):
    acc = _wa.get_account_for_user(ctx["user"]["id"])
    return acc or {"linked": False}


@router.delete("/api/whatsapp/account")
def whatsapp_unlink(ctx: dict = Depends(get_current_context)):
    _wa.unlink_account(ctx["user"]["id"])
    return {"ok": True}


@router.get("/api/whatsapp/bridge-secret")
def whatsapp_bridge_secret(user: dict = Depends(get_current_user)):
    """The shared secret the Node bridge needs. Owner/admin only."""
    if user["role"] != "admin":
        raise HTTPException(403, "Admin only")
    return {"secret": _wa.get_bridge_secret()}


@router.post("/api/whatsapp/inbound")
async def whatsapp_inbound(request: Request):
    """
    Receive an incoming WhatsApp message from the local Node bridge.
    Protected by X-Nexus-Secret header (the same value the bridge reads from
    its .env). Returns a JSON reply the bridge sends back over WhatsApp.
    """
    secret = request.headers.get("X-Nexus-Secret", "")
    _wa.verify_bridge_secret(secret)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid JSON body")

    phone = (body.get("from") or "").strip()
    text = (body.get("text") or "").strip()
    message_id = (body.get("message_id") or "").strip()

    if len(text) > 4000:
        text = text[:4000]

    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None, lambda: _wa.handle_inbound(phone, text, message_id),
    )
    return result


@router.post("/api/whatsapp/inbound-audio")
async def whatsapp_inbound_audio(
    request: Request,
    file: UploadFile = File(...),
    sender: str = Form(..., alias="from"),
    message_id: str = Form(""),
):
    """
    Receive a WhatsApp voice note from the bridge, transcribe it locally with
    faster-whisper, then route the transcript through the same agent path as
    a typed message — so conversation memory, link-codes, business switching
    all work identically.
    """
    _wa.verify_bridge_secret(request.headers.get("X-Nexus-Secret", ""))

    phone, account = _resolve_phone(sender)
    # Allow voice for unlinked phones too — but the only thing they can do is
    # say their link code. We transcribe first so we can hand it to the same
    # link-code path the text inbound uses.

    if _wa._is_duplicate(message_id):
        return {"text": "", "attachments": [], "silent": True}

    # Save the audio to a temp file (capped) and convert to wav for whisper.
    suffix = Path(file.filename or "voice.ogg").suffix or ".ogg"
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    try:
        size = 0
        while True:
            chunk = await file.read(64 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > _MAX_MEDIA_BYTES:
                tmp.close()
                Path(tmp.name).unlink(missing_ok=True)
                raise HTTPException(413, f"Voice note too large (max {_MAX_MEDIA_BYTES // (1024*1024)} MB)")
            tmp.write(chunk)
        tmp.close()

        wav_path = _ffmpeg_to_wav(tmp.name, suffix)

        from voice.listener import _transcribe
        loop = asyncio.get_event_loop()
        text = await loop.run_in_executor(None, lambda: (_transcribe(wav_path) or "").strip())

        if wav_path != tmp.name:
            Path(wav_path).unlink(missing_ok=True)
    except HTTPException:
        raise
    except Exception:
        logger.exception("[WhatsApp] voice transcription failed")
        Path(tmp.name).unlink(missing_ok=True)
        return {
            "text": "Sorry — I couldn't transcribe that voice note. Try sending it as text?",
            "attachments": [],
        }
    finally:
        Path(tmp.name).unlink(missing_ok=True)

    if not text:
        return {
            "text": "I couldn't catch what you said in that voice note. Could you try again, or send it as text?",
            "attachments": [],
        }

    # Route the transcript through the same handler as a text message so
    # all the linking, memory, and agent logic apply uniformly.
    result = await asyncio.get_event_loop().run_in_executor(
        None, lambda: _wa.handle_inbound(phone, text, message_id),
    )
    # Prefix with what we heard so the user can spot mis-transcriptions early.
    if result.get("text") and not result.get("silent"):
        result["text"] = f"_(heard: \"{text[:140]}\")_\n\n" + result["text"]
    return result


@router.post("/api/whatsapp/inbound-document")
async def whatsapp_inbound_document(
    request: Request,
    file: UploadFile = File(...),
    sender: str = Form(..., alias="from"),
    message_id: str = Form(""),
    mime_type: str = Form(""),
):
    """
    Receive a PDF (or text-like document) sent over WhatsApp, run AI doc-intake,
    and return a friendly summary. PDF text extraction + LLM call both stay
    local — sensitive=True (matches the doc_intake router contract).

    Images / scans aren't supported yet (we don't ship OCR). The user gets a
    polite nudge to send the PDF version instead.
    """
    _wa.verify_bridge_secret(request.headers.get("X-Nexus-Secret", ""))

    phone, account = _resolve_phone(sender)
    if not account:
        return _UNLINKED_PROMPT

    if _wa._is_duplicate(message_id):
        return {"text": "", "attachments": [], "silent": True}

    name = (file.filename or "").lower()
    mime = (mime_type or file.content_type or "").lower()
    is_pdf = name.endswith(".pdf") or "pdf" in mime
    is_image = mime.startswith("image/") or any(name.endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp", ".heic"))

    if is_image and not is_pdf:
        return {
            "text": (
                "I can read PDFs and pasted text, but I don't OCR photos yet. "
                "If that was a photo of a document, try sending the PDF version "
                "or paste the text into the chat."
            ),
            "attachments": [],
        }

    # Read with hard cap.
    buf = bytearray()
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > _MAX_MEDIA_BYTES:
            raise HTTPException(413, f"File too large (max {_MAX_MEDIA_BYTES // (1024*1024)} MB)")
    if not buf:
        raise HTTPException(400, "Empty file.")

    # Extract text. Reuse doc_intake's helpers — sensitive=True is enforced inside.
    from api.routers import doc_intake as _di
    if is_pdf:
        try:
            text = _di._pdf_to_text(bytes(buf))
        except HTTPException as he:
            return {"text": he.detail or "Couldn't read that file.", "attachments": []}
        if not text.strip():
            return {
                "text": (
                    "That PDF doesn't have any embedded text — looks like a scan or image-only PDF. "
                    "Paste the text in chat and I'll extract the fields."
                ),
                "attachments": [],
            }
    else:
        try:
            text = bytes(buf).decode("utf-8", errors="ignore")
        except Exception:
            return {"text": "Couldn't read that file as text or PDF.", "attachments": []}

    if len(text.strip()) < 30:
        return {"text": "Not enough text in that document to extract anything useful.", "attachments": []}

    loop = asyncio.get_event_loop()
    try:
        extraction = await loop.run_in_executor(None, lambda: _di._extract_via_llm(text))
    except HTTPException as he:
        return {"text": he.detail or "Couldn't extract fields from that document.", "attachments": []}
    except Exception as e:
        logger.exception("[WhatsApp] doc intake failed")
        return {"text": f"Sorry — couldn't extract that document: {e}", "attachments": []}

    # Format a chatty summary for WhatsApp.
    reply = _format_doc_extraction(extraction, file.filename or "document")
    return {"text": reply, "attachments": []}


def _format_doc_extraction(extraction: dict, filename: str) -> str:
    """Turn doc_intake's structured output into a friendly WhatsApp reply."""
    doc_type = (extraction.get("doc_type") or "other").replace("_", " ")
    summary  = extraction.get("summary") or ""
    parties  = extraction.get("parties") or []
    dates    = extraction.get("dates") or []
    amounts  = extraction.get("amounts") or []

    lines = [f"📄 *Got that {doc_type}* — `{filename}`"]
    if summary:
        lines.append(summary)
    if parties:
        lines.append(f"\n*Parties:* {', '.join(parties[:4])}")
    if amounts:
        amt_lines = [f"  • {a.get('label', 'amount')}: {a.get('value', '')} {a.get('currency', '')}".rstrip()
                     for a in amounts[:5]]
        lines.append("\n*Amounts:*\n" + "\n".join(amt_lines))
    if dates:
        date_lines = [f"  • {d.get('label', 'date')}: {d.get('value', '')}" for d in dates[:5]]
        lines.append("\n*Dates:*\n" + "\n".join(date_lines))
    if not (summary or parties or amounts or dates):
        lines.append("Couldn't pull any structured fields — the document may need a different format.")

    out = "\n".join(lines)
    return out[:3850] + ("\n\n…(truncated)" if len(out) > 3850 else "")


@router.get("/api/whatsapp/attachment")
def whatsapp_attachment(path: str, request: Request):
    """
    Serve a generated file to the bridge so it can forward it over WhatsApp.
    Protected by X-Nexus-Secret. Only files inside outputs/ are served.
    """
    _wa.verify_bridge_secret(request.headers.get("X-Nexus-Secret", ""))

    from config.settings import OUTPUTS_DIR
    try:
        absolute = Path(path).resolve()
        absolute.relative_to(Path(OUTPUTS_DIR).resolve())
    except (ValueError, OSError):
        raise HTTPException(400, "Path outside of outputs/")
    if not absolute.is_file():
        raise HTTPException(404, "File not found")

    ext = absolute.suffix.lower()
    mime = "application/pdf" if ext == ".pdf" \
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document" \
        if ext == ".docx" else "application/octet-stream"
    return FileResponse(str(absolute), filename=absolute.name, media_type=mime)
