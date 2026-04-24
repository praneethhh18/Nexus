"""
Self-hosted first-run setup wizard (9.3).

Drives the `/setup` page on a fresh install — before any user has signed up.
Unauthenticated by design: the whole point is that there's no account yet.
Once setup is marked complete, the endpoints gate further access so a
returning user can't re-run the wizard and reconfigure model defaults.

Writes a tiny `nexus_setup` single-row table tracking completion state +
the selected model. Runtime Ollama probing talks to the daemon over the
configured `OLLAMA_BASE_URL` — same URL the rest of the app uses.
"""
from __future__ import annotations

import os
import platform
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from loguru import logger

from config.settings import DB_PATH, OLLAMA_BASE_URL


TABLE = "nexus_setup"

# Recommended models by available RAM tier. A fresh user gets the closest
# fit for their machine; they can override on the final step.
RECOMMENDED_MODELS: List[Dict[str, Any]] = [
    {
        "name":       "qwen2.5:3b-instruct-q4_K_M",
        "label":      "Qwen 2.5 3B — lightweight",
        "min_ram_gb": 4,
        "size_gb":    2.0,
        "note":       "Fastest on an older laptop. Decent for chat; weaker on long SQL.",
    },
    {
        "name":       "llama3.1:8b-instruct-q4_K_M",
        "label":      "Llama 3.1 8B — balanced (recommended)",
        "min_ram_gb": 8,
        "size_gb":    4.7,
        "note":       "Good all-round default. Handles the orchestrator + agent loop well.",
    },
    {
        "name":       "qwen2.5:14b-instruct-q4_K_M",
        "label":      "Qwen 2.5 14B — heavier",
        "min_ram_gb": 16,
        "size_gb":    9.0,
        "note":       "Sharper reasoning if you have the RAM.",
    },
]


# ── Storage ────────────────────────────────────────────────────────────────
def _conn() -> sqlite3.Connection:
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE} (
            id               INTEGER PRIMARY KEY CHECK (id = 1),
            completed        INTEGER NOT NULL DEFAULT 0,
            completed_at     TEXT,
            chosen_model     TEXT,
            install_notes    TEXT
        )
    """)
    conn.execute(
        f"INSERT OR IGNORE INTO {TABLE} (id, completed) VALUES (1, 0)"
    )
    conn.commit()
    return conn


def _row() -> Dict:
    conn = _conn()
    conn.row_factory = sqlite3.Row
    try:
        r = conn.execute(f"SELECT * FROM {TABLE} WHERE id = 1").fetchone()
    finally:
        conn.close()
    return dict(r) if r else {}


# ── Platform probes ────────────────────────────────────────────────────────
def _detect_ram_gb() -> Optional[float]:
    """Best-effort RAM detection. Returns None if we can't tell."""
    try:
        import psutil  # type: ignore
        return round(psutil.virtual_memory().total / (1024 ** 3), 1)
    except Exception:
        pass
    # Fall back to /proc/meminfo on Linux
    try:
        with open("/proc/meminfo", "r") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    kb = int(line.split()[1])
                    return round(kb / (1024 ** 2), 1)
    except Exception:
        return None
    return None


def _probe_ollama() -> Dict[str, Any]:
    try:
        r = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=1.5)
        if r.status_code == 200:
            data = r.json()
            models = [m.get("name") for m in (data.get("models") or [])]
            return {"online": True, "host": OLLAMA_BASE_URL, "models": models}
        return {"online": False, "host": OLLAMA_BASE_URL, "error": f"HTTP {r.status_code}"}
    except Exception as e:
        return {"online": False, "host": OLLAMA_BASE_URL, "error": str(e)}


def _disk_free_gb() -> Optional[float]:
    try:
        _, _, free = shutil.disk_usage(str(Path(DB_PATH).parent))
        return round(free / (1024 ** 3), 1)
    except Exception:
        return None


# ── Wizard steps ───────────────────────────────────────────────────────────
def status() -> Dict[str, Any]:
    """Full snapshot of the install's readiness — consumed by the wizard UI."""
    row = _row()
    ollama = _probe_ollama()
    ram_gb = _detect_ram_gb()
    disk_gb = _disk_free_gb()

    # Filter recommendations by detected RAM. If unknown, show all.
    suitable = []
    for m in RECOMMENDED_MODELS:
        if ram_gb is None or ram_gb >= m["min_ram_gb"]:
            suitable.append({**m, "recommended": m["name"] == "llama3.1:8b-instruct-q4_K_M"})

    # A model counts as "installed" if its base name (before the colon) or full
    # name appears in the Ollama model list — users sometimes have the same
    # family at different quantisations.
    installed_names = set(ollama.get("models") or [])
    for m in suitable:
        base = m["name"].split(":", 1)[0]
        m["installed"] = any(n == m["name"] or n.startswith(base + ":") for n in installed_names)

    chosen = row.get("chosen_model")
    default_model = chosen or next(
        (m["name"] for m in suitable if m.get("recommended")),
        suitable[0]["name"] if suitable else "llama3.1:8b-instruct-q4_K_M",
    )

    # Gate: the user can finish setup only when Ollama is online AND the
    # chosen model is either installed or one of the recommended names.
    chosen_installed = chosen in installed_names if chosen else False
    can_finish = ollama.get("online") and (chosen_installed or any(m["installed"] for m in suitable))

    return {
        "completed":     bool(row.get("completed")),
        "completed_at":  row.get("completed_at"),
        "platform": {
            "os":      platform.system(),
            "release": platform.release(),
            "arch":    platform.machine(),
            "python":  platform.python_version(),
            "ram_gb":  ram_gb,
            "disk_free_gb": disk_gb,
        },
        "ollama":       ollama,
        "models": {
            "suitable":        suitable,
            "chosen":          chosen,
            "default_model":   default_model,
            "install_hint_url": "https://ollama.com/download",
        },
        "can_finish":   can_finish,
    }


def pull_model(name: str) -> Dict[str, Any]:
    """
    Trigger an Ollama `pull` for `name`. The Ollama API streams progress;
    we consume it server-side and return a final summary. The UI polls
    `status()` after this to see the new model appear in `ollama.models`.
    """
    if not name or not isinstance(name, str):
        raise ValueError("model name is required")
    if ":" not in name and "/" not in name:
        # Defensive: reject names that don't look like model refs
        raise ValueError("model name must include a tag, e.g. 'llama3.1:8b-instruct-q4_K_M'")
    try:
        r = requests.post(
            f"{OLLAMA_BASE_URL}/api/pull",
            json={"name": name, "stream": False},
            timeout=60 * 10,  # up to 10 min for a cold pull
        )
        r.raise_for_status()
        return {"ok": True, "model": name, "body": r.json() if r.content else {}}
    except Exception as e:
        logger.warning(f"[setup_wizard] pull_model({name}) failed: {e}")
        return {"ok": False, "model": name, "error": str(e)}


def choose_model(name: str) -> Dict[str, Any]:
    """Record the user's model choice. Takes effect on next LLM call."""
    if not name:
        raise ValueError("model name is required")
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET chosen_model = ? WHERE id = 1",
            (name,),
        )
        conn.commit()
    finally:
        conn.close()
    # Also set an env var so the current process picks it up without a restart.
    os.environ["OLLAMA_MODEL"] = name
    return status()


def complete() -> Dict[str, Any]:
    """Mark setup done. Idempotent."""
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET completed = 1, completed_at = ? WHERE id = 1",
            (datetime.utcnow().isoformat(),),
        )
        conn.commit()
    finally:
        conn.close()
    return status()


def reset() -> Dict[str, Any]:
    """Flag setup as incomplete again — used by admin tooling."""
    conn = _conn()
    try:
        conn.execute(
            f"UPDATE {TABLE} SET completed = 0, completed_at = NULL WHERE id = 1"
        )
        conn.commit()
    finally:
        conn.close()
    return status()


def is_complete() -> bool:
    return bool(_row().get("completed"))
