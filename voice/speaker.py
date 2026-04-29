"""
Voice Speaker — text-to-speech using pyttsx3 (fully offline).
"""
from __future__ import annotations

import threading

from loguru import logger

_engine = None
_engine_lock = threading.Lock()


def _get_engine():
    global _engine
    if _engine is None:
        try:
            import pyttsx3
            _engine = pyttsx3.init()
            _engine.setProperty("rate", 150)   # words per minute
            _engine.setProperty("volume", 0.9)

            # Try to pick a clear voice
            voices = _engine.getProperty("voices")
            if voices:
                # Prefer female voice on Windows for clarity
                for v in voices:
                    if "zira" in v.name.lower() or "female" in v.name.lower():
                        _engine.setProperty("voice", v.id)
                        break

            logger.info("[Speaker] pyttsx3 initialized, rate=150 wpm")
        except Exception as e:
            logger.warning(f"[Speaker] pyttsx3 init failed: {e}")
            _engine = None
    return _engine


def _truncate_for_speech(text: str, max_sentences: int = 3) -> str:
    """Truncate long text to first N sentences for speech output."""
    sentences = text.replace("!\n", "! ").replace(".\n", ". ").split(". ")
    return ". ".join(sentences[:max_sentences]).strip() + "."


def speak(text: str) -> bool:
    """Speak text using pyttsx3. Returns True if successful."""
    if not text or not text.strip():
        return False

    engine = _get_engine()
    if engine is None:
        logger.warning("[Speaker] TTS unavailable. Printing instead.")
        print(f"\n[NexusAgent says]: {text}\n")
        return False

    try:
        with _engine_lock:
            spoken_text = _truncate_for_speech(text, max_sentences=3)
            engine.say(spoken_text)
            engine.runAndWait()
        return True
    except Exception as e:
        logger.warning(f"[Speaker] speak() failed: {e}")
        return False


def speak_alert(text: str) -> bool:
    """Speak an alert with slightly faster rate for urgency."""
    engine = _get_engine()
    if engine:
        try:
            with _engine_lock:
                engine.setProperty("rate", 175)
                engine.say(f"Alert! {_truncate_for_speech(text, 2)}")
                engine.runAndWait()
                engine.setProperty("rate", 150)
            return True
        except Exception as e:
            logger.warning(f"[Speaker] speak_alert() failed: {e}")
    print(f"\n[ALERT]: {text}\n")
    return False


def is_available() -> bool:
    """Check if TTS is functional."""
    try:
        import pyttsx3
        e = pyttsx3.init()
        e.stop()
        return True
    except Exception:
        return False
