"""
NexusAgent Settings — loads and validates all configuration from .env
Includes comprehensive startup validation and clear error reporting.
"""
import os
from pathlib import Path
from dotenv import load_dotenv
from loguru import logger

# Load .env from project root (two levels up from this file)
_ROOT = Path(__file__).parent.parent
load_dotenv(_ROOT / ".env")


def _get(key: str, default=None, required: bool = False):
    val = os.getenv(key, default)
    if required and not val:
        raise ValueError(f"Required config key '{key}' is not set. Check your .env file.")
    return val


# ── Ollama ──────────────────────────────────────────────────────────────────
OLLAMA_BASE_URL: str = _get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL: str = _get("OLLAMA_MODEL", "llama3.1:8b-instruct-q4_K_M")
OLLAMA_FALLBACK_MODEL: str = _get("OLLAMA_FALLBACK_MODEL", "qwen2.5:3b-instruct-q4_K_M")
EMBED_MODEL: str = _get("EMBED_MODEL", "nomic-embed-text:latest")

# ── Email ────────────────────────────────────────────────────────────────────
GMAIL_USER: str = _get("GMAIL_USER", "")
GMAIL_APP_PASSWORD: str = _get("GMAIL_APP_PASSWORD", "")
EMAIL_ENABLED: bool = bool(GMAIL_USER and GMAIL_APP_PASSWORD)

# ── Discord ──────────────────────────────────────────────────────────────────
DISCORD_WEBHOOK_URL: str = _get("DISCORD_WEBHOOK_URL", "")
DISCORD_ENABLED: bool = bool(DISCORD_WEBHOOK_URL)

# ── Slack ────────────────────────────────────────────────────────────────────
SLACK_WEBHOOK_URL: str = _get("SLACK_WEBHOOK_URL", "")
SLACK_ENABLED: bool = bool(SLACK_WEBHOOK_URL)

# ── Database ─────────────────────────────────────────────────────────────────
DB_PATH: str = str(_ROOT / _get("DB_PATH", "data/nexusagent.db"))
CHROMA_PATH: str = str(_ROOT / "chroma_db")

# ── Directories ───────────────────────────────────────────────────────────────
OUTPUTS_DIR: str = str(_ROOT / "outputs")
REPORTS_DIR: str = str(_ROOT / "outputs" / "reports")
EMAIL_DRAFTS_DIR: str = str(_ROOT / "outputs" / "email_drafts")
DOCUMENTS_DIR: str = str(_ROOT / "data" / "documents")
AUDIT_LOG_PATH: str = str(_ROOT / "outputs" / "audit_log.json")

# ── App behaviour ─────────────────────────────────────────────────────────────
LOG_LEVEL: str = _get("LOG_LEVEL", "INFO")
ANOMALY_THRESHOLD: float = float(_get("ANOMALY_THRESHOLD", "0.15"))
MONITOR_INTERVAL_MINUTES: int = int(_get("MONITOR_INTERVAL_MINUTES", "60"))
MAX_SQL_RETRIES: int = int(_get("MAX_SQL_RETRIES", "3"))
MAX_REFLECTION_RETRIES: int = int(_get("MAX_REFLECTION_RETRIES", "2"))
SQL_QUERY_TIMEOUT_SECONDS: float = float(_get("SQL_QUERY_TIMEOUT_SECONDS", "30"))
SQL_MAX_ROWS: int = int(_get("SQL_MAX_ROWS", "10000"))
TOP_K_RETRIEVAL: int = int(_get("TOP_K_RETRIEVAL", "5"))
CHUNK_SIZE: int = int(_get("CHUNK_SIZE", "500"))
CHUNK_OVERLAP: int = int(_get("CHUNK_OVERLAP", "50"))

# ── Version ───────────────────────────────────────────────────────────────────
VERSION: str = "2.0.0"


def validate_config() -> dict:
    """Check all settings and return a status dict with detailed diagnostics."""
    issues = []
    warnings = []

    # Critical checks
    if not OLLAMA_BASE_URL:
        issues.append("OLLAMA_BASE_URL is missing — Ollama server URL is required")
    if not OLLAMA_MODEL:
        issues.append("OLLAMA_MODEL is missing — at least one LLM model must be configured")

    # Connection check (non-blocking)
    try:
        import requests
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=3)
        if resp.status_code == 200:
            models = [m["name"] for m in resp.json().get("models", [])]
            if not any(OLLAMA_MODEL in m for m in models):
                warnings.append(
                    f"Model '{OLLAMA_MODEL}' not found in Ollama. "
                    f"Pull it with: ollama pull {OLLAMA_MODEL}"
                )
            if not any(EMBED_MODEL in m for m in models):
                warnings.append(
                    f"Embedding model '{EMBED_MODEL}' not found. "
                    f"Pull it with: ollama pull {EMBED_MODEL}"
                )
        else:
            warnings.append(f"Ollama returned HTTP {resp.status_code}")
    except requests.ConnectionError:
        warnings.append("Ollama is not running. Start it with: ollama serve")
    except Exception as e:
        warnings.append(f"Ollama connectivity check failed: {e}")

    # Optional features
    if not EMAIL_ENABLED:
        warnings.append("Email disabled (GMAIL_USER/GMAIL_APP_PASSWORD not set) - email drafts saved to disk")
    if not DISCORD_ENABLED:
        warnings.append("Discord disabled (DISCORD_WEBHOOK_URL not set) - desktop notifications active")

    # Validate numeric ranges
    if MAX_SQL_RETRIES < 0 or MAX_SQL_RETRIES > 10:
        warnings.append(f"MAX_SQL_RETRIES={MAX_SQL_RETRIES} seems unusual (typical: 1-5)")
    if CHUNK_SIZE < 100 or CHUNK_SIZE > 5000:
        warnings.append(f"CHUNK_SIZE={CHUNK_SIZE} outside recommended range (100-5000)")
    if CHUNK_OVERLAP >= CHUNK_SIZE:
        issues.append(f"CHUNK_OVERLAP ({CHUNK_OVERLAP}) must be less than CHUNK_SIZE ({CHUNK_SIZE})")

    for msg in warnings:
        logger.warning(f"[Config] {msg}")
    for msg in issues:
        logger.error(f"[Config] {msg}")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "warnings": warnings,
        "email_enabled": EMAIL_ENABLED,
        "discord_enabled": DISCORD_ENABLED,
        "ollama_model": OLLAMA_MODEL,
        "embed_model": EMBED_MODEL,
        "version": VERSION,
    }


def ensure_directories():
    """Create all required output directories if they don't exist."""
    dirs = [OUTPUTS_DIR, REPORTS_DIR, EMAIL_DRAFTS_DIR, DOCUMENTS_DIR,
            CHROMA_PATH, str(Path(DB_PATH).parent)]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
