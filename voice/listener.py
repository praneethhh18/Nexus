"""
Voice Listener — records audio from microphone and transcribes with faster-whisper.
Falls back to text input if microphone or whisper is unavailable.
"""
from __future__ import annotations

import os
import tempfile
import time
from typing import Optional

from loguru import logger


def _record_audio(duration: int = 5, sample_rate: int = 16000) -> Optional[str]:
    """Record audio from the default microphone. Returns path to WAV file."""
    try:
        import sounddevice as sd
        import soundfile as sf

        print(f"\nRecording for {duration} seconds...", end="", flush=True)
        for remaining in range(duration, 0, -1):
            print(f" {remaining}", end="", flush=True)
            time.sleep(1)
        print(" Done!")

        audio = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
        )
        sd.wait()

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        sf.write(tmp.name, audio, sample_rate)
        return tmp.name

    except Exception as e:
        logger.warning(f"[Listener] Recording failed: {e}")
        return None


SUPPORTED_LANGUAGES = ("en", "hi", "auto")

# Module-level model cache. The Whisper model takes ~10s to load on first
# use (downloads weights to disk first time, then loads them into memory).
# We were creating a fresh WhisperModel on every transcribe call — every
# voice turn paid the full cold-load cost. Caching it here drops the
# steady-state per-call time from ~12s to ~1s.
_model = None
_model_lock = None


def _get_model():
    global _model, _model_lock
    if _model is not None:
        return _model
    # Lazy threading import — keeps module import path light at server boot.
    import threading
    if _model_lock is None:
        _model_lock = threading.Lock()
    with _model_lock:
        if _model is not None:
            return _model
        from faster_whisper import WhisperModel
        logger.info("[Listener] Loading Whisper model (base/int8)…")
        _model = WhisperModel("base", device="cpu", compute_type="int8")
        logger.success("[Listener] Whisper model ready")
        return _model


def prewarm() -> bool:
    """Load Whisper at startup so the first voice turn isn't a 10s cold-load.
    Safe to call from a daemon thread on boot — fails quietly if the model
    isn't installed."""
    try:
        _get_model()
        return True
    except Exception as e:
        logger.warning(f"[Listener] Whisper prewarm skipped: {e}")
        return False


def _transcribe(wav_path: str, language: str = "en") -> Optional[str]:
    """
    Transcribe a WAV file using faster-whisper (local, no API).

    language:
        'en'   — English (default)
        'hi'   — Hindi (Whisper handles natively)
        'auto' — Let Whisper detect; useful for mixed-language users
    """
    if language not in SUPPORTED_LANGUAGES:
        language = "en"
    try:
        model = _get_model()
        kwargs = {"beam_size": 5}
        if language != "auto":
            kwargs["language"] = language
        segments, info = model.transcribe(wav_path, **kwargs)
        text = " ".join(s.text for s in segments).strip()
        if text:
            logger.info(f"[Listener] Transcribed ({language}): '{text[:80]}'")
            return text
        return None
    except Exception as e:
        logger.warning(f"[Listener] Transcription failed: {e}")
        return None


def listen(duration: int = 5) -> Optional[str]:
    """
    Record from microphone and return transcribed text.
    Returns None on any failure (UI handles fallback messaging).
    """
    if not is_available():
        logger.warning("[Listener] No audio input device detected.")
        return None

    wav_path = _record_audio(duration)

    if wav_path:
        try:
            text = _transcribe(wav_path)
            if text:
                return text
            logger.warning("[Listener] Transcription returned empty text.")
            return None
        finally:
            try:
                os.unlink(wav_path)
            except Exception:
                pass

    logger.warning("[Listener] Recording failed — no audio captured.")
    return None


def is_available() -> bool:
    """Check if voice recording and transcription are available."""
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        has_input = any(d["max_input_channels"] > 0 for d in devices)
        return has_input
    except Exception:
        return False
