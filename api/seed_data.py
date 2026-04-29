"""
One-shot sample-data seeder.

Gives a fresh business realistic mock data so every page on the app shows
something meaningful on first open instead of an empty state. The AI
features (lead scoring, BANT, follow-up nudges, Forge verification banner)
also light up because the seed includes:

  - workspace ICP description (so Score-this-lead actually works)
  - lead scores + reasons on a handful of contacts
  - one BANT-extracted contact with a suggested stage advance
  - source variety on contacts (manual / public_form / email_paste /
    ai_outbound / referral) so the Leads tab filters have something to do
  - an "(unknown)" AI-prospected contact so the Forge verify banner shows
  - interactions on most contacts, with one stale one (>7 days back) that
    triggers the smart follow-up nudge
  - an intake key so the Public Form panel isn't empty

Safety: idempotent. If the business already has any contacts, companies,
or deals, we refuse to seed to avoid polluting real data.
"""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Dict, List

from api import crm as _crm
from api import tasks as _tasks
from api import invoices as _inv
from config.settings import DB_PATH


def _has_existing_data(business_id: str) -> bool:
    """Refuse to seed if the business already has CRM data."""
    try:
        if _crm.list_companies(business_id, limit=1):
            return True
        if _crm.list_contacts(business_id, limit=1):
            return True
        if _crm.list_deals(business_id, limit=1):
            return True
    except Exception:
        pass
    return False


COMPANIES = [
    {"name": "TechCorp Solutions",    "industry": "Technology",       "size": "50-200",   "website": "techcorp.example.com"},
    {"name": "Bangalore Coffee Co",   "industry": "Food & Beverage",  "size": "10-50",    "website": "bangalorecoffee.example.com"},
    {"name": "Stellar Retail",        "industry": "Retail",           "size": "200-1000", "website": "stellar.example.com"},
    {"name": "Innovate Labs",         "industry": "R&D",              "size": "10-50",    "website": "innovatelabs.example.com"},
]

CONTACTS_FOR_COMPANY = [
    ("TechCorp Solutions",   {"first_name": "Priya",  "last_name": "Sharma",    "title": "Head of Learning",      "email": "priya@techcorp.example.com",    "phone": "+91 98765 10001"}),
    ("TechCorp Solutions",   {"first_name": "Rohit",  "last_name": "Menon",     "title": "VP Engineering",        "email": "rohit@techcorp.example.com",    "phone": "+91 98765 10002"}),
    ("Bangalore Coffee Co",  {"first_name": "Anjali", "last_name": "Krishnan",  "title": "Founder",               "email": "anjali@bangalorecoffee.example.com", "phone": "+91 98765 20001"}),
    ("Stellar Retail",       {"first_name": "Arjun",  "last_name": "Patel",     "title": "Training Manager",      "email": "arjun@stellar.example.com",     "phone": "+91 98765 30001"}),
    ("Innovate Labs",        {"first_name": "Meera",  "last_name": "Iyer",      "title": "Chief of Staff",        "email": "meera@innovatelabs.example.com","phone": "+91 98765 40001"}),
]

# (company, deal_name, stage, value_inr, probability_pct)
DEALS = [
    ("TechCorp Solutions",   "Leadership coaching — Q2 cohort",   "proposal",    450000, 60),
    ("Bangalore Coffee Co",  "Barista certification programme",   "negotiation", 180000, 80),
    ("Stellar Retail",       "Sales-floor training rollout",      "qualified",   320000, 40),
    ("Innovate Labs",        "Team offsite facilitation",         "lead",         90000, 20),
    ("TechCorp Solutions",   "Onboarding curriculum revamp",      "won",         275000, 100),
]

# (title, priority, status, due_offset_days)  — offset of 0 = today, -N = overdue
def _tasks_spec() -> List[Dict]:
    return [
        {"title": "Follow up with Priya on cohort proposal", "priority": "high",   "status": "open",         "due_offset": 0},
        {"title": "Send invoice reminder to Stellar Retail", "priority": "normal", "status": "open",         "due_offset": -2},
        {"title": "Draft barista curriculum — Module 3",     "priority": "high",   "status": "in_progress",  "due_offset": 3},
        {"title": "Review Q1 attendance numbers",            "priority": "normal", "status": "open",         "due_offset": 7},
        {"title": "Prep workshop handouts for Friday",       "priority": "normal", "status": "open",         "due_offset": 4},
        {"title": "Confirm venue for Innovate offsite",      "priority": "low",    "status": "open",         "due_offset": 10},
    ]


def _invoice_specs():
    today = date.today()
    return [
        {
            "customer": "TechCorp Solutions",
            "issue": (today - timedelta(days=14)).isoformat(),
            "due":   (today + timedelta(days=16)).isoformat(),
            "status": "sent",
            "line_items": [
                {"description": "Leadership coaching — April",  "quantity": 1, "unit_price": 275000},
            ],
            "tax_pct": 18,
        },
        {
            "customer": "Bangalore Coffee Co",
            "issue": (today - timedelta(days=45)).isoformat(),
            "due":   (today - timedelta(days=15)).isoformat(),  # overdue
            "status": "sent",
            "line_items": [
                {"description": "Barista certification — batch 1", "quantity": 1, "unit_price": 90000},
                {"description": "Course materials",                "quantity": 12, "unit_price": 1500},
            ],
            "tax_pct": 18,
        },
        {
            "customer": "Stellar Retail",
            "issue": (today - timedelta(days=60)).isoformat(),
            "due":   (today - timedelta(days=30)).isoformat(),
            "status": "paid",
            "line_items": [
                {"description": "Floor-staff training — pilot", "quantity": 1, "unit_price": 120000},
            ],
            "tax_pct": 18,
        },
        {
            "customer": "Innovate Labs",
            "issue": today.isoformat(),
            "due":   (today + timedelta(days=30)).isoformat(),
            "status": "draft",
            "line_items": [
                {"description": "Team offsite facilitation (draft)", "quantity": 1, "unit_price": 90000},
            ],
            "tax_pct": 18,
        },
    ]


SAMPLE_ICP = (
    "Mid-market companies (50-500 employees) in India running customer-facing "
    "teams that need structured training. Decision-makers are L&D heads, VPs "
    "of People, or founders. Budget signal: existing training spend or recent "
    "hiring growth. Sweet spot: companies that have outgrown ad-hoc onboarding "
    "but aren't big enough for an in-house L&D function yet."
)


# Lead scores attached to specific contacts. Email is the lookup key so
# we don't depend on insertion order. Only contacts named here are scored.
SAMPLE_SCORES = {
    "priya@techcorp.example.com": {
        "score": 88, "reason": "L&D head at a mid-market tech company — exact ICP fit. Existing budget signal in the proposal we sent.",
    },
    "rohit@techcorp.example.com": {
        "score": 64, "reason": "VP Eng at the same account — strong influence but not the budget owner. Useful champion.",
    },
    "anjali@bangalorecoffee.example.com": {
        "score": 72, "reason": "Founder of a 50-person F&B chain. Right segment, slightly small for our usual ACV. Active deal already in negotiation.",
    },
    "arjun@stellar.example.com": {
        "score": 45, "reason": "Training manager at a large retail chain — bigger than our sweet spot, decision cycle is long.",
    },
    "meera@innovatelabs.example.com": {
        "score": 35, "reason": "Chief of staff at a small R&D outfit — interesting, but they typically run training in-house.",
    },
}


SAMPLE_BANT_TARGET_EMAIL = "anjali@bangalorecoffee.example.com"
SAMPLE_BANT = {
    "budget":    {"signal": "yes",     "evidence": "we have approval for the Q2 cohort budget"},
    "authority": {"signal": "yes",     "evidence": "I sign off on training spend"},
    "need":      {"signal": "yes",     "evidence": "current onboarding takes too long, we're losing baristas in week 2"},
    "timing":    {"signal": "unknown", "evidence": "depends on when we can free up our floor leads"},
    "confidence": 70,
    "suggested_stage": "negotiation",
    "summary": "Strong B/A/N — timing is the only thing pending. Worth pushing pricing.",
}


# (company_name, contact_email_hint, source_label) — sets contact.source so
# the Leads-tab source filter has variety to show.
SAMPLE_SOURCES = {
    "priya@techcorp.example.com":              "manual",
    "rohit@techcorp.example.com":              "referral",
    "anjali@bangalorecoffee.example.com":      "public_form",
    "arjun@stellar.example.com":               "email_paste",
    "meera@innovatelabs.example.com":          "manual",
}


# Forge-style AI-prospected contact — first_name="(unknown)" so the
# verify banner on Contact detail surfaces the moment the user opens it.
FORGE_CANDIDATE = {
    "company":    "Innovate Labs",
    "first_name": "(unknown)",
    "last_name":  "",
    "title":      "Head of People",
    "email":      "",
    "source":     "ai_outbound",
    "notes":      "AI-prospected by Forge — verify the actual person at this role before reaching out.",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _set_contact_columns(business_id: str, contact_id: str, **cols) -> None:
    """Set new-ish columns on a contact row that may not exist on every
    schema (source, lead_score, lead_score_reason, lead_scored_at,
    bant_signals, bant_extracted_at). Skips fields whose columns aren't
    present yet — graceful for schemas predating the migration."""
    if not cols:
        return
    conn = sqlite3.connect(DB_PATH)
    try:
        present = {r[1] for r in conn.execute("PRAGMA table_info(nexus_contacts)").fetchall()}
        usable = {k: v for k, v in cols.items() if k in present}
        if not usable:
            return
        sets = ", ".join(f"{k} = ?" for k in usable)
        params = list(usable.values()) + [contact_id, business_id]
        conn.execute(
            f"UPDATE nexus_contacts SET {sets} WHERE id = ? AND business_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()


def _seed_icp(business_id: str, user_id: str) -> bool:
    """Write the workspace ICP. Defensive — creates the table if needed."""
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nexus_workspace_settings (
                business_id      TEXT PRIMARY KEY,
                icp_description  TEXT DEFAULT '',
                icp_updated_at   TEXT,
                icp_updated_by   TEXT
            )
        """)
        conn.execute(
            """INSERT INTO nexus_workspace_settings
                  (business_id, icp_description, icp_updated_at, icp_updated_by)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(business_id) DO UPDATE SET
                  icp_description = excluded.icp_description,
                  icp_updated_at  = excluded.icp_updated_at,
                  icp_updated_by  = excluded.icp_updated_by""",
            (business_id, SAMPLE_ICP, _now_iso(), user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return True


def _seed_intake_key(business_id: str, user_id: str) -> bool:
    """Create one demo intake key so the public-form panel has something
    to display. Mirrors api/routers/intake._generate_raw_key shape."""
    raw = "nx_intake_" + secrets.token_urlsafe(24)
    key_id = uuid.uuid4().hex
    prefix = raw[:12] + "…"
    sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nexus_intake_keys (
                id           TEXT PRIMARY KEY,
                business_id  TEXT NOT NULL,
                key_hash     TEXT NOT NULL UNIQUE,
                key_prefix   TEXT NOT NULL,
                label        TEXT DEFAULT '',
                created_at   TEXT NOT NULL,
                created_by   TEXT,
                revoked_at   TEXT,
                last_used_at TEXT,
                use_count    INTEGER DEFAULT 0
            )
        """)
        conn.execute(
            """INSERT INTO nexus_intake_keys
                  (id, business_id, key_hash, key_prefix, label, created_at, created_by)
                  VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (key_id, business_id, sha, prefix, "Demo public form", _now_iso(), user_id),
        )
        conn.commit()
    finally:
        conn.close()
    return True


def _seed_interactions(business_id: str, user_id: str,
                       contact_ids_by_email: Dict[str, str]) -> int:
    """Add a handful of interactions so the Timeline panel has content
    AND so the smart follow-up nudge has something to fire on (the stale
    one below is intentionally 12 days back)."""
    today = datetime.now(timezone.utc)
    samples = [
        # (contact_email, type, subject, summary, days_ago)
        ("priya@techcorp.example.com",            "email",   "Re: Q2 cohort proposal",
         "Sent through the leadership coaching proposal with three pricing tiers. Priya asked about the smaller cohort option specifically.", 12),  # stale → nudge
        ("priya@techcorp.example.com",            "call",    "Discovery call",
         "Walked through their current onboarding pain points. They're losing engineers in the first month — clear need.", 21),
        ("rohit@techcorp.example.com",            "meeting", "Engineering team intro",
         "Met Rohit and two of his leads. They're sceptical about cohort-based programmes — prefer self-paced.", 9),
        ("anjali@bangalorecoffee.example.com",    "email",   "Pricing follow-up",
         "Anjali replied confirming budget approval and asking about timeline. Strong qualified signal.", 3),
        ("anjali@bangalorecoffee.example.com",    "note",    "Stage advance: qualified → negotiation",
         "Moved to negotiation after the budget-confirmed reply.", 3),
        ("arjun@stellar.example.com",             "email",   "Cold inbound from Stellar",
         "Arjun pasted their current training breakdown and asked if we could replicate it at scale.", 5),
    ]
    count = 0
    for email, itype, subject, summary, days_ago in samples:
        cid = contact_ids_by_email.get(email)
        if not cid:
            continue
        when = (today - timedelta(days=days_ago)).isoformat()
        try:
            _crm.create_interaction(business_id, user_id, {
                "type": itype, "subject": subject, "summary": summary,
                "contact_id": cid, "occurred_at": when,
            })
            count += 1
        except Exception:
            # Don't let a single interaction failure abort the whole seed.
            continue
    return count


def seed_sample_data(business_id: str, user_id: str) -> Dict:
    """Insert all sample records for `business_id`. Idempotent."""
    if _has_existing_data(business_id):
        return {
            "seeded": False,
            "reason": "Business already has CRM data — sample seeding skipped to protect real records.",
        }

    by_name: Dict[str, str] = {}  # company name → id
    for c in COMPANIES:
        row = _crm.create_company(business_id, user_id, c)
        by_name[c["name"]] = row["id"]

    contact_ids_by_company: Dict[str, List[str]] = {}
    contact_ids_by_email: Dict[str, str] = {}
    for company_name, data in CONTACTS_FOR_COMPANY:
        payload = dict(data)
        payload["company_id"] = by_name.get(company_name)
        row = _crm.create_contact(business_id, user_id, payload)
        contact_ids_by_company.setdefault(company_name, []).append(row["id"])
        if data.get("email"):
            contact_ids_by_email[data["email"]] = row["id"]

    # Tag contacts with source labels + lead scores so the Leads tab and
    # the AI fit assessment panel have content to render.
    for email, src in SAMPLE_SOURCES.items():
        cid = contact_ids_by_email.get(email)
        if not cid:
            continue
        cols = {"source": src}
        sc = SAMPLE_SCORES.get(email)
        if sc:
            cols.update({
                "lead_score": sc["score"],
                "lead_score_reason": sc["reason"],
                "lead_scored_at": _now_iso(),
            })
        _set_contact_columns(business_id, cid, **cols)

    # BANT card on the negotiation-stage contact so the qualification view
    # is non-empty out of the box.
    bant_cid = contact_ids_by_email.get(SAMPLE_BANT_TARGET_EMAIL)
    if bant_cid:
        _set_contact_columns(
            business_id, bant_cid,
            bant_signals=json.dumps(SAMPLE_BANT),
            bant_extracted_at=_now_iso(),
        )

    # AI-prospected "(unknown)" contact so the Forge verification banner
    # appears the moment a user opens that contact's detail page.
    forge_cid = None
    try:
        forge_payload = {
            "first_name": FORGE_CANDIDATE["first_name"],
            "last_name":  FORGE_CANDIDATE["last_name"],
            "title":      FORGE_CANDIDATE["title"],
            "email":      FORGE_CANDIDATE["email"],
            "notes":      FORGE_CANDIDATE["notes"],
            "company_id": by_name.get(FORGE_CANDIDATE["company"]),
        }
        forge_row = _crm.create_contact(business_id, user_id, forge_payload)
        forge_cid = forge_row["id"]
        _set_contact_columns(business_id, forge_cid, source=FORGE_CANDIDATE["source"])
    except Exception:
        pass

    for company_name, name, stage, value, prob in DEALS:
        _crm.create_deal(business_id, user_id, {
            "name": name, "stage": stage,
            "value": value, "currency": "INR",
            "probability_pct": prob,
            "company_id": by_name.get(company_name),
            "contact_id": (contact_ids_by_company.get(company_name) or [None])[0],
        })

    today = date.today()
    for t in _tasks_spec():
        due = (today + timedelta(days=t["due_offset"])).isoformat()
        _tasks.create_task(business_id, user_id, {
            "title": t["title"], "priority": t["priority"],
            "status": t["status"], "due_date": due,
        })

    for spec in _invoice_specs():
        co_name = spec["customer"]
        _inv.create_invoice(business_id, user_id, {
            "customer_company_id": by_name.get(co_name),
            "customer_name": co_name,
            "issue_date": spec["issue"],
            "due_date":   spec["due"],
            "status":     spec["status"],
            "line_items": spec["line_items"],
            "tax_pct":    spec["tax_pct"],
            "currency":   "INR",
        })

    # Workspace-level extras: ICP description + an intake key.
    try:
        _seed_icp(business_id, user_id)
        icp_seeded = True
    except Exception:
        icp_seeded = False
    try:
        _seed_intake_key(business_id, user_id)
        intake_seeded = True
    except Exception:
        intake_seeded = False

    interactions_count = _seed_interactions(business_id, user_id, contact_ids_by_email)

    return {
        "seeded": True,
        "counts": {
            "companies":     len(COMPANIES),
            "contacts":      len(CONTACTS_FOR_COMPANY) + (1 if forge_cid else 0),
            "deals":         len(DEALS),
            "tasks":         len(_tasks_spec()),
            "invoices":      len(_invoice_specs()),
            "interactions":  interactions_count,
            "icp":           1 if icp_seeded else 0,
            "intake_keys":   1 if intake_seeded else 0,
        },
    }
