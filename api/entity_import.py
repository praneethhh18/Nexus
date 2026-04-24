"""
Entity import — map CSV/Excel columns to contact / task / invoice fields and
insert rows through the regular CRUD functions (so validation + indexes fire).

Flow the UI runs:

    1. POST /api/entity-import/preview
          body = {path: str, entity_type: 'contact'|'task'|'invoice'}
       → returns detected columns + sample rows + auto-suggested mapping.
    2. POST /api/entity-import/commit
          body = {path, entity_type, mapping: {target_field: source_column}}
       → inserts the rows, returns {inserted, skipped, errors}.

No temp tables; no `imported_*` tables get created. The file is read fresh
on each call (the user's filesystem, server-side temp dir, etc). The import
ignores rows missing a required field and keeps going rather than failing the
whole batch — with counts + first 10 error messages returned.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger


# Field catalog per entity type — drives auto-mapping and the UI form.
ENTITY_FIELDS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "contact": {
        "first_name":   {"label": "First name", "required": True},
        "last_name":    {"label": "Last name"},
        "email":        {"label": "Email"},
        "phone":        {"label": "Phone"},
        "title":        {"label": "Job title"},
        "company_name": {"label": "Company name (text, matches by name)"},
        "tags":         {"label": "Tags (comma-separated)"},
        "notes":        {"label": "Notes"},
    },
    "task": {
        "title":       {"label": "Title", "required": True},
        "description": {"label": "Description"},
        "priority":    {"label": "Priority (low/normal/high/urgent)"},
        "status":      {"label": "Status (open/in_progress/done/cancelled)"},
        "due_date":    {"label": "Due date (YYYY-MM-DD)"},
        "tags":        {"label": "Tags (comma-separated)"},
    },
    "invoice": {
        "customer_name":  {"label": "Customer name", "required": True},
        "customer_email": {"label": "Customer email"},
        "total":          {"label": "Total amount (creates a single line item)"},
        "currency":       {"label": "Currency (e.g. USD, INR)"},
        "issue_date":     {"label": "Issue date (YYYY-MM-DD)"},
        "due_date":       {"label": "Due date (YYYY-MM-DD)"},
        "notes":          {"label": "Notes"},
    },
}


# ── File reading ────────────────────────────────────────────────────────────
def _read_df(path: str) -> pd.DataFrame:
    p = Path(path)
    ext = p.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(path)
    if ext in (".xlsx", ".xls"):
        return pd.read_excel(path)
    raise ValueError(f"Unsupported file type: {ext}")


def _normalize_col(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", str(name).lower())


def _auto_map(source_columns: List[str], entity_type: str) -> Dict[str, str]:
    """Best-effort guess of target→source based on fuzzy name match."""
    fields = ENTITY_FIELDS.get(entity_type, {})
    norm_source = {_normalize_col(c): c for c in source_columns}
    mapping: Dict[str, str] = {}
    for target in fields.keys():
        key = _normalize_col(target)
        # Exact match
        if key in norm_source:
            mapping[target] = norm_source[key]
            continue
        # Partial match (substring either way)
        hit = next((orig for norm, orig in norm_source.items() if key in norm or norm in key), None)
        if hit:
            mapping[target] = hit
    # Common aliases
    aliases = {
        "first_name":   ["fname", "given", "firstname"],
        "last_name":    ["lname", "family", "lastname", "surname"],
        "email":        ["emailaddress", "mail"],
        "phone":        ["mobile", "tel", "phonenumber"],
        "company_name": ["organization", "employer", "company"],
        "customer_name": ["client", "customer"],
    }
    for target, candidates in aliases.items():
        if target in mapping:
            continue
        for alias in candidates:
            if alias in norm_source:
                mapping[target] = norm_source[alias]
                break
    return mapping


# ── Preview ─────────────────────────────────────────────────────────────────
def preview(path: str, entity_type: str, sample_rows: int = 5) -> Dict:
    if entity_type not in ENTITY_FIELDS:
        raise ValueError(f"Unknown entity_type '{entity_type}' — must be one of {list(ENTITY_FIELDS)}")
    df = _read_df(path)
    cols = [str(c) for c in df.columns]
    return {
        "entity_type":     entity_type,
        "source_columns":  cols,
        "sample_rows":     df.head(sample_rows).fillna("").astype(str).to_dict(orient="records"),
        "total_rows":      int(len(df)),
        "target_fields":   ENTITY_FIELDS[entity_type],
        "suggested_mapping": _auto_map(cols, entity_type),
    }


# ── Commit ──────────────────────────────────────────────────────────────────
def _coerce_value(v) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _row_to_payload(row: pd.Series, mapping: Dict[str, str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for target, source in mapping.items():
        if not source or source not in row.index:
            continue
        out[target] = _coerce_value(row[source])
    return out


def _resolve_company(business_id: str, name: str) -> Optional[str]:
    if not name:
        return None
    import sqlite3
    from config.settings import DB_PATH
    conn = sqlite3.connect(DB_PATH)
    try:
        row = conn.execute(
            "SELECT id FROM nexus_companies "
            "WHERE business_id = ? AND name = ? COLLATE NOCASE LIMIT 1",
            (business_id, name),
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None


def _insert_contact(business_id: str, user_id: str, payload: Dict) -> None:
    from api import crm as _crm
    if not payload.get("first_name") and not payload.get("last_name"):
        raise ValueError("Contact needs at least a first or last name")
    # Optional: bind to company by name (don't create companies implicitly)
    company_name = payload.pop("company_name", None)
    if company_name:
        cid = _resolve_company(business_id, company_name)
        if cid:
            payload["company_id"] = cid
    _crm.create_contact(business_id, user_id, payload)


def _insert_task(business_id: str, user_id: str, payload: Dict) -> None:
    from api import tasks as _tasks
    if not payload.get("title"):
        raise ValueError("Task needs a title")
    _tasks.create_task(business_id, user_id, payload)


def _insert_invoice(business_id: str, user_id: str, payload: Dict) -> None:
    from api import invoices as _inv
    if not payload.get("customer_name"):
        raise ValueError("Invoice needs a customer name")
    # If a total is given, turn it into a single line item; skip if line_items already exist.
    total = payload.pop("total", None)
    if total and not payload.get("line_items"):
        try:
            amount = float(total)
        except (TypeError, ValueError):
            amount = 0
        payload["line_items"] = [
            {"description": "Imported", "quantity": 1, "unit_price": amount}
        ]
    _inv.create_invoice(business_id, user_id, payload)


_INSERTERS: Dict[str, Callable[[str, str, Dict], None]] = {
    "contact": _insert_contact,
    "task":    _insert_task,
    "invoice": _insert_invoice,
}


def commit(business_id: str, user_id: str, path: str, entity_type: str,
           mapping: Dict[str, str], max_errors_returned: int = 10) -> Dict:
    """Run the import. Returns {inserted, skipped, errors}."""
    if entity_type not in _INSERTERS:
        raise ValueError(f"Unknown entity_type '{entity_type}'")
    # Validate required fields are mapped
    fields = ENTITY_FIELDS[entity_type]
    for target, meta in fields.items():
        if meta.get("required") and not mapping.get(target):
            raise ValueError(f"Required field '{target}' is not mapped to any column")

    df = _read_df(path)
    inserter = _INSERTERS[entity_type]
    inserted = 0
    skipped = 0
    errors: List[str] = []
    for idx, row in df.iterrows():
        payload = _row_to_payload(row, mapping)
        try:
            inserter(business_id, user_id, payload)
            inserted += 1
        except Exception as e:
            skipped += 1
            if len(errors) < max_errors_returned:
                errors.append(f"row {idx + 2}: {e}")  # +2 = header + 0-based
    return {
        "entity_type": entity_type,
        "inserted": inserted,
        "skipped": skipped,
        "errors": errors,
        "total": inserted + skipped,
    }
