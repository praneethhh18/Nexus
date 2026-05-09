"""Lead Hunter — automated B2B lead generation.

Finds businesses matching the user's query, dedups against existing CRM
contacts, and optionally auto-creates contacts. The current source is
OpenStreetMap (free, no API key, decent Indian SMB coverage); the search
function is pluggable so a Google Places / JustDial / IndiaMART backend
can be swapped in later via env var.

Usage from WhatsApp / chat:
    "find catering services in Bengaluru"
    "find logistics companies near Pune, add the top 10 to my CRM"
    "find textile manufacturers in Surat with phone numbers"

Returned leads always include name + address. Phone, website, and email
come from OSM tags when available — generally ~30-50% of Indian results
have a phone in the data; less for email. The tool surfaces the gap so
the user can fill blanks via Vox/Iris later.
"""
from __future__ import annotations

import os
import re
import sqlite3  # sqlite3.Row sentinel
import time
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from agents.tool_registry import register_tool
from config.db import get_conn
from utils.timez import now_iso

# Tag every Lead Hunter import with this so the user can filter the segment
# in the CRM ("source = lead-hunter") for outreach campaigns.
LEAD_TAG = "lead-hunter"
USER_AGENT = "NexusAgent/1.0 (https://nexusagent.in; AI assistant for Indian SMBs)"


# ── Nominatim (OpenStreetMap) backend ──────────────────────────────────────
def _search_nominatim(query: str, location: str, max_results: int) -> List[Dict[str, Any]]:
    """Free, key-less B2B search against OpenStreetMap.

    Nominatim is rate-limited: 1 req/sec, must include a User-Agent header
    identifying the application, and we should cache where reasonable.
    https://operations.osmfoundation.org/policies/nominatim/
    """
    q = f"{query.strip()} {location.strip()}".strip()
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        "q":              q,
        "format":         "json",
        "limit":          max(1, min(50, max_results)),
        "addressdetails": "1",
        "extratags":      "1",  # exposes phone / website / contact:* / opening_hours
    }

    try:
        with httpx.Client(timeout=20.0, headers={"User-Agent": USER_AGENT}) as client:
            r = client.get(url, params=params)
        if r.status_code != 200:
            logger.warning(f"[lead_hunter] Nominatim HTTP {r.status_code}: {r.text[:200]}")
            return []
        rows = r.json() or []
    except Exception as e:
        logger.warning(f"[lead_hunter] Nominatim request failed: {e}")
        return []

    leads: List[Dict[str, Any]] = []
    for row in rows:
        tags = row.get("extratags") or {}
        addr = row.get("address") or {}

        # Phone may live under several OSM keys depending on mapper preference
        phone = (tags.get("phone")
                 or tags.get("contact:phone")
                 or tags.get("mobile")
                 or "").strip()
        website = (tags.get("website")
                   or tags.get("contact:website")
                   or tags.get("url")
                   or "").strip()
        email = (tags.get("email")
                 or tags.get("contact:email")
                 or "").strip()

        # Construct a clean, human-friendly address
        addr_parts = [
            addr.get("house_number"),
            addr.get("road"),
            addr.get("suburb") or addr.get("neighbourhood"),
            addr.get("city") or addr.get("town") or addr.get("village"),
            addr.get("state"),
        ]
        clean_address = ", ".join(p for p in addr_parts if p) or row.get("display_name", "")

        name = (row.get("namedetails", {}).get("name")
                if isinstance(row.get("namedetails"), dict) else "")
        if not name:
            # Fall back to first comma-separated chunk of display_name
            name = (row.get("display_name") or "").split(",")[0].strip()
        if not name:
            continue

        leads.append({
            "name":       name[:200],
            "phone":      _normalize_in_phone(phone),
            "email":      email[:200],
            "website":    website[:300],
            "address":    clean_address[:500],
            "category":   tags.get("amenity") or tags.get("shop") or tags.get("office") or "",
            "lat":        row.get("lat"),
            "lng":        row.get("lon"),
            "source":     "openstreetmap",
            "source_id":  f"osm:{row.get('osm_type','?')}:{row.get('osm_id','?')}",
        })
    return leads


# ── Phone normalization ─────────────────────────────────────────────────────
# OSM phone tags often contain multiple numbers ("+91...; +91...") and various
# whitespace / separator patterns. Take the first valid one.
def _normalize_in_phone(phone: str) -> str:
    if not phone:
        return ""
    # Split on common multi-value separators OSM uses
    candidates = re.split(r"[;,/]+|\s{2,}", phone)
    for raw in candidates:
        s = re.sub(r"[^\d+]", "", raw or "")
        if not s:
            continue
        # Strip a stray leading + if it's followed by another +
        if s.count("+") > 1:
            s = "+" + s.replace("+", "")
        if s.startswith("+"):
            if len(s) >= 9:
                return s
            continue
        if len(s) == 10:                       # bare 10-digit Indian mobile
            return "+91" + s
        if len(s) == 11 and s.startswith("0"):  # leading-zero local
            return "+91" + s[1:]
        if len(s) == 12 and s.startswith("91"):
            return "+" + s
        if len(s) >= 8:
            return "+" + s
    return ""


# ── De-dup against existing CRM contacts ───────────────────────────────────
def _existing_phone_set(business_id: str) -> set:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        from api.crm import CONTACTS_TABLE
        rows = conn.execute(
            f"SELECT phone FROM {CONTACTS_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    out = set()
    for r in rows:
        digits = re.sub(r"\D", "", (r["phone"] or ""))
        if len(digits) >= 10:
            out.add(digits[-10:])  # last 10 = the part that's stable across formats
    return out


def _existing_name_set(business_id: str) -> set:
    """Lowercased exact-name index — secondary fallback when phones are missing."""
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    try:
        from api.crm import CONTACTS_TABLE
        rows = conn.execute(
            f"SELECT first_name, last_name FROM {CONTACTS_TABLE} WHERE business_id = ?",
            (business_id,),
        ).fetchall()
    finally:
        conn.close()
    return {f"{(r['first_name'] or '').strip()} {(r['last_name'] or '').strip()}".strip().lower()
            for r in rows}


def _is_duplicate(lead: Dict[str, Any], phone_idx: set, name_idx: set) -> bool:
    digits = re.sub(r"\D", "", lead.get("phone") or "")
    if len(digits) >= 10 and digits[-10:] in phone_idx:
        return True
    return lead["name"].strip().lower() in name_idx


# ── The tool ───────────────────────────────────────────────────────────────
def _find_leads(ctx: Dict[str, Any], args: Dict[str, Any]) -> Dict[str, Any]:
    business_id = ctx["business_id"]
    user_id     = ctx["user_id"]

    query    = (args.get("query") or "").strip()
    location = (args.get("location") or "").strip()
    if not query or not location:
        raise ValueError("Both 'query' (e.g. 'catering services') and 'location' "
                         "(e.g. 'Bengaluru') are required.")

    max_results  = max(1, min(50, int(args.get("max_results", 25))))
    auto_create  = bool(args.get("auto_create", False))
    require_phone = bool(args.get("require_phone", False))

    raw = _search_nominatim(query, location, max_results)
    if require_phone:
        raw = [l for l in raw if l.get("phone")]

    phone_idx = _existing_phone_set(business_id)
    name_idx  = _existing_name_set(business_id)

    fresh: List[Dict[str, Any]] = []
    skipped_dupes: int = 0
    for lead in raw:
        if _is_duplicate(lead, phone_idx, name_idx):
            skipped_dupes += 1
            continue
        fresh.append(lead)

    created_ids: List[str] = []
    if auto_create and fresh:
        from api import crm as _crm
        for lead in fresh:
            try:
                # Split the business name into first/last for the existing schema.
                # Companies-as-contacts isn't ideal but matches the current model;
                # a future refactor can split into proper `companies` rows.
                name = lead["name"]
                first, _, rest = name.partition(" ")
                payload = {
                    "first_name": first[:80] or "Lead",
                    "last_name":  (rest or "")[:80] or None,
                    "phone":      lead.get("phone") or "",
                    "email":      lead.get("email") or "",
                    "title":      (lead.get("category") or "")[:120],
                    "notes":      (
                        f"Found by Lead Hunter: query={query!r} location={location!r}\n"
                        f"Address: {lead.get('address','—')}\n"
                        f"Website: {lead.get('website','—')}\n"
                        f"Source: {lead.get('source')} ({lead.get('source_id','—')})"
                    )[:2000],
                    "tags":       LEAD_TAG,
                }
                c = _crm.create_contact(business_id, user_id, payload)
                created_ids.append(c.get("id", ""))
            except Exception as e:
                logger.warning(f"[lead_hunter] failed to create contact for {lead.get('name')}: {e}")

    summary_msg = (
        f"Found {len(raw)} {'leads' if len(raw) != 1 else 'lead'} for "
        f"'{query}' in '{location}'. "
        f"{len(fresh)} new, {skipped_dupes} already in your CRM."
    )
    if auto_create:
        summary_msg += f" Created {len(created_ids)} new contact(s)."
    elif fresh:
        summary_msg += " Reply 'add them all' to import."

    # Trim the lead detail returned to the LLM so the conversation context
    # doesn't blow up on a 50-result preview.
    preview = [
        {
            "name":     l["name"],
            "phone":    l.get("phone") or "—",
            "address":  l.get("address", "")[:120],
            "website":  l.get("website") or "",
            "category": l.get("category") or "",
        }
        for l in fresh[:15]
    ]

    return {
        "ok":             True,
        "found":          len(raw),
        "new":            len(fresh),
        "skipped_dupes":  skipped_dupes,
        "created":        len(created_ids),
        "created_ids":    created_ids,
        "leads_preview":  preview,
        "more":           max(0, len(fresh) - len(preview)),
        "message":        summary_msg,
    }


register_tool(
    name="find_leads",
    description=(
        "Search for new business leads (potential customers) by industry/type "
        "and location. Returns matching businesses with name, phone, address, "
        "and website. De-duplicates against existing CRM contacts. Use this "
        "when the user asks to find leads, prospects, or new customers — e.g. "
        "'find catering services in Bengaluru' or 'find textile manufacturers "
        "in Surat with phone numbers'. By default returns a preview list; set "
        "auto_create=true to import them as CRM contacts (tagged 'lead-hunter')."
    ),
    input_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Industry / business type to search for. e.g. 'catering "
                    "services', 'logistics companies', 'CA firms', 'hospitals'."
                ),
            },
            "location": {
                "type": "string",
                "description": (
                    "City / region to search in. e.g. 'Bengaluru', 'Pune', "
                    "'Mumbai', 'Surat'. Indian cities recommended for best results."
                ),
            },
            "max_results": {
                "type": "integer",
                "description": "Max leads to return (1-50). Default 25.",
                "default": 25,
            },
            "auto_create": {
                "type": "boolean",
                "description": (
                    "If true, automatically import all new leads as CRM "
                    "contacts. If false (default), return a preview only — "
                    "the user must confirm before import."
                ),
                "default": False,
            },
            "require_phone": {
                "type": "boolean",
                "description": "If true, only return leads that have a phone number.",
                "default": False,
            },
        },
        "required": ["query", "location"],
    },
    handler=_find_leads,
    summary_fn=lambda a: (
        f"Lead Hunter: {a.get('query','?')} in {a.get('location','?')}"
        + (" (import)" if a.get("auto_create") else " (preview)")
    ),
)
