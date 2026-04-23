"""
Workflow Storage — save/load/list/delete workflows as JSON files.
Each workflow is one JSON file in workflows/saved/ and is scoped to a business.
"""
from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from loguru import logger

SAVED_DIR = Path(__file__).parent / "saved"
API_KEYS_FILE = Path(__file__).parent / "api_keys.json"


def _ensure_dir():
    SAVED_DIR.mkdir(parents=True, exist_ok=True)


def _workflow_path(wf_id: str) -> Path:
    return SAVED_DIR / f"{wf_id}.json"


# ── Workflow CRUD ─────────────────────────────────────────────────────────────

def save_workflow(wf: Dict[str, Any], business_id: str = "default", user_id: str = "default") -> str:
    """Save or update a workflow. Returns workflow id."""
    _ensure_dir()
    if "id" not in wf or not wf["id"]:
        wf["id"] = f"wf-{uuid.uuid4().hex[:8]}"
    if "created_at" not in wf:
        wf["created_at"] = datetime.now().isoformat()
    wf["updated_at"] = datetime.now().isoformat()
    wf.setdefault("enabled", False)
    wf.setdefault("run_count", 0)
    wf.setdefault("last_run", None)
    wf.setdefault("last_status", None)
    wf.setdefault("nodes", [])
    wf.setdefault("edges", [])
    # Stamp business on first save; never overwrite once set
    wf.setdefault("business_id", business_id)
    wf.setdefault("created_by", user_id)

    path = _workflow_path(wf["id"])
    path.write_text(json.dumps(wf, indent=2, default=str), encoding="utf-8")
    logger.info(f"[Storage] Saved workflow '{wf.get('name')}' ({wf['id']}) biz={wf['business_id']}")
    return wf["id"]


def load_workflow(wf_id: str, business_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Load a workflow. If business_id is given, enforce it matches."""
    path = _workflow_path(wf_id)
    if not path.exists():
        return None
    try:
        wf = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        logger.error(f"[Storage] Failed to load {wf_id}: {e}")
        return None

    if business_id is not None:
        wf_biz = wf.get("business_id", "default")
        if wf_biz != business_id and wf_biz != "default":
            return None  # hide cross-tenant
    return wf


def list_workflows(business_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Return workflows for the given business (or all if None), sorted by name."""
    _ensure_dir()
    wfs = []
    for f in SAVED_DIR.glob("*.json"):
        try:
            wf = json.loads(f.read_text(encoding="utf-8"))
            if business_id is not None:
                wf_biz = wf.get("business_id", "default")
                if wf_biz != business_id and wf_biz != "default":
                    continue
            wfs.append(wf)
        except Exception:
            pass
    return sorted(wfs, key=lambda w: w.get("name", ""))


def delete_workflow(wf_id: str, business_id: Optional[str] = None) -> bool:
    wf = load_workflow(wf_id, business_id=business_id)
    if not wf:
        return False
    path = _workflow_path(wf_id)
    if path.exists():
        path.unlink()
        logger.info(f"[Storage] Deleted workflow {wf_id}")
        return True
    return False


def toggle_enabled(wf_id: str, enabled: bool, business_id: Optional[str] = None) -> bool:
    wf = load_workflow(wf_id, business_id=business_id)
    if not wf:
        return False
    wf["enabled"] = enabled
    save_workflow(wf, business_id=wf.get("business_id", "default"), user_id=wf.get("created_by", "default"))
    return True


def update_run_stats(wf_id: str, status: str) -> None:
    wf = load_workflow(wf_id)
    if not wf:
        return
    wf["last_run"] = datetime.now().isoformat()
    wf["last_status"] = status
    wf["run_count"] = wf.get("run_count", 0) + 1
    save_workflow(wf, business_id=wf.get("business_id", "default"), user_id=wf.get("created_by", "default"))


# ── API Keys Store ────────────────────────────────────────────────────────────

def load_api_keys() -> Dict[str, str]:
    if not API_KEYS_FILE.exists():
        return {}
    try:
        return json.loads(API_KEYS_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {}


def save_api_key(name: str, value: str) -> None:
    keys = load_api_keys()
    keys[name] = value
    API_KEYS_FILE.write_text(json.dumps(keys, indent=2), encoding="utf-8")
    logger.info(f"[Storage] API key saved: {name}")


def delete_api_key(name: str) -> None:
    keys = load_api_keys()
    keys.pop(name, None)
    API_KEYS_FILE.write_text(json.dumps(keys, indent=2), encoding="utf-8")


def get_api_key(name: str) -> str:
    return load_api_keys().get(name, "")
