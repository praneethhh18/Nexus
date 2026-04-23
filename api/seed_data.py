"""
One-shot sample-data seeder.

Gives a fresh business realistic mock data — 4 companies, 6 contacts,
5 deals across the pipeline, 6 tasks (today / upcoming / overdue),
4 invoices in different states — so the Dashboard and every CRM/Tasks/
Invoices page show something meaningful on first open instead of empty
states.

Safety: idempotent. If the business already has *any* contacts, companies,
or deals, we refuse to seed to avoid polluting real data.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Dict, List

from api import crm as _crm
from api import tasks as _tasks
from api import invoices as _inv


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
    for company_name, data in CONTACTS_FOR_COMPANY:
        payload = dict(data)
        payload["company_id"] = by_name.get(company_name)
        row = _crm.create_contact(business_id, user_id, payload)
        contact_ids_by_company.setdefault(company_name, []).append(row["id"])

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

    return {
        "seeded": True,
        "counts": {
            "companies": len(COMPANIES),
            "contacts":  len(CONTACTS_FOR_COMPANY),
            "deals":     len(DEALS),
            "tasks":     len(_tasks_spec()),
            "invoices":  len(_invoice_specs()),
        },
    }
