"""
Voice transcription endpoints. The shared upload-and-transcribe shape is
used by two flows: a generic /transcribe (returns text) and the
voice-memo-to-task shortcut that auto-creates a task from the transcript.

Both convert .webm/.ogg/.mp4/.m4a to 16kHz mono WAV via ffmpeg before
handing the file to whisper, falling back to the raw upload if ffmpeg
isn't on the PATH.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from loguru import logger

from api.auth import get_current_context

router = APIRouter(tags=["voice"])


async def _save_audio_temp(file: UploadFile) -> tuple[str, str]:
    """Persist the uploaded blob to a temp file and return (path, suffix)."""
    suffix = Path(file.filename or "audio.webm").suffix or ".webm"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:
            raise HTTPException(413, "Audio too large (max 25 MB)")
        tmp.write(content)
        return tmp.name, suffix


def _to_wav(tmp_path: str, suffix: str) -> str:
    """Convert browser-recorded audio to 16kHz mono WAV. Returns the path that
    should be transcribed (the original if conversion isn't available)."""
    if suffix.lower() not in (".webm", ".ogg", ".mp4", ".m4a"):
        return tmp_path
    try:
        wav_path = tmp_path.replace(suffix, ".wav")
        subprocess.run(
            ["ffmpeg", "-i", tmp_path, "-ar", "16000", "-ac", "1", wav_path, "-y"],
            capture_output=True, timeout=10,
        )
        return wav_path
    except Exception:
        return tmp_path


@router.post("/api/voice/memo-to-task")
async def voice_memo_to_task(
    file: UploadFile = File(...),
    language: str = Query("en"),
    ctx: dict = Depends(get_current_context),
):
    """
    Transcribe a voice memo and create a task directly from it.
    First sentence becomes the title, the rest becomes the description.
    """
    tmp_path, suffix = await _save_audio_temp(file)
    wav_path = _to_wav(tmp_path, suffix)

    try:
        from voice.listener import _transcribe
        text = (_transcribe(wav_path, language=language) or "").strip()
        if not text:
            raise HTTPException(400, "Could not transcribe audio — try recording again")

        parts = text.split(". ", 1)
        title = parts[0][:200].rstrip(".")
        description = (parts[1] if len(parts) > 1 else "").strip()[:4000]

        from api import tasks as _tasks
        task = _tasks.create_task(
            ctx["business_id"], ctx["user"]["id"],
            {"title": title, "description": description, "priority": "normal"},
        )
        return {"task": task, "transcript": text}
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        if wav_path != tmp_path:
            Path(wav_path).unlink(missing_ok=True)


@router.post("/api/voice/transcribe")
async def transcribe_voice(
    file: UploadFile = File(...),
    language: str = Query("en"),
    ctx: dict = Depends(get_current_context),
):
    tmp_path, suffix = await _save_audio_temp(file)
    wav_path = _to_wav(tmp_path, suffix)

    try:
        from voice.listener import _transcribe
        text = _transcribe(wav_path, language=language)
        return {"text": text or "", "success": bool(text), "language": language}
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return {"text": "", "success": False, "error": str(e)}
    finally:
        Path(tmp_path).unlink(missing_ok=True)
        if wav_path != tmp_path:
            Path(wav_path).unlink(missing_ok=True)
