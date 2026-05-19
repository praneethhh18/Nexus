"""Industry-flavoured sample data seeder.

Why this module exists:
    The old `seed_data.py` produces one fixed dataset (a training/L&D business).
    Onboarding now collects the customer's industry — so when a Healthcare or
    Real-estate user finishes the wizard, the right move is to drop realistic
    seed data IN THEIR DOMAIN, not training-cohort data. That turns "empty
    workspace" into "workspace that already speaks your language."

Design:
    INDUSTRY_DATA defines compact dicts per industry — companies, contacts,
    deals (whatever the industry calls them), tasks, invoices, optional ICP
    blurb. We re-use the existing CRM/invoice/task service helpers so:
      • all the audit columns get populated correctly
      • the seed survives schema changes that hit those tables
      • the seed is multi-tenant safe by construction

Safety:
    Idempotent. If the business already has any contacts/companies/deals
    we refuse to seed — same guard as seed_data.py. Tested side-by-side
    so the two seeders never both run on the same workspace.

Coverage today:
    11 industries (matches PRESETS in industry_setup.py).
    Falls back to the generic seed_data.py if industry is "Other" / unknown.

Future:
    More industries → add to INDUSTRY_DATA. The framework doesn't care.
    Industry-specific lead scores / BANT signals → mirror seed_data.py.
"""
from __future__ import annotations

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger

from api import crm as _crm
from api import tasks as _tasks
from api import invoices as _inv


# ── Data per industry ─────────────────────────────────────────────────────
#
# Each entry needs:
#   icp           — one-line ideal-customer description used by lead scoring
#   companies     — 3-5 organisations (the "accounts" in this industry)
#   contacts      — 5-7 people, mapped by (company_name, person_dict)
#   deals         — 3-5 active deals/cases/appointments (industry-appropriate
#                   labels go in the deal name; stage/value/probability are
#                   standard CRM enums so the pipeline view still works)
#   tasks         — 5-7 to-dos with `due_offset` in days (- = overdue)
#   invoices      — 3-4 with line items, tax, and a mix of statuses
#                   (one overdue, one paid, one draft, one current)
#
# Currency is INR throughout — Indian SMB target. `unit_price` values are
# realistic for that industry's price range so the dashboard KPIs read true.

INDUSTRY_DATA: Dict[str, Dict[str, Any]] = {
    # ── Healthcare ────────────────────────────────────────────────────────
    "Healthcare": {
        "icp": (
            "Independent clinics, multi-specialty centres, and diagnostic labs "
            "(5-50 staff) across Indian Tier-1/Tier-2 cities. Decision-makers "
            "are practitioners, clinic owners, or practice managers."
        ),
        "companies": [
            {"name": "Apollo Family Clinic",      "industry": "Healthcare", "size": "10-50", "website": "apollofamily.example.in"},
            {"name": "WellSpring Diagnostics",    "industry": "Healthcare", "size": "10-50", "website": "wellspring.example.in"},
            {"name": "MediCare Speciality Centre","industry": "Healthcare", "size": "50-200","website": "medicare.example.in"},
            {"name": "Saanvi Dental Studio",      "industry": "Healthcare", "size": "1-10",  "website": "saanvi.example.in"},
        ],
        "contacts": [
            ("Apollo Family Clinic",       {"first_name": "Asha",    "last_name": "Nair",     "title": "Practice Manager",     "email": "asha@apollofamily.example.in",     "phone": "+91 98450 11001"}),
            ("Apollo Family Clinic",       {"first_name": "Rohan",   "last_name": "Iyer",     "title": "Senior Physician",     "email": "rohan@apollofamily.example.in",    "phone": "+91 98450 11002"}),
            ("WellSpring Diagnostics",     {"first_name": "Kavya",   "last_name": "Reddy",    "title": "Lab Coordinator",      "email": "kavya@wellspring.example.in",      "phone": "+91 98450 22001"}),
            ("MediCare Speciality Centre", {"first_name": "Dr. Vinay","last_name": "Shenoy",  "title": "Cardiologist",         "email": "vinay@medicare.example.in",        "phone": "+91 98450 33001"}),
            ("Saanvi Dental Studio",       {"first_name": "Saanvi",  "last_name": "Pillai",   "title": "Founder / Dentist",    "email": "saanvi@saanvi.example.in",         "phone": "+91 98450 44001"}),
        ],
        "deals": [
            ("Apollo Family Clinic",        "Annual health-check programme — 3 corporates", "proposal",    240000, 60),
            ("WellSpring Diagnostics",      "Home-collection service rollout",              "negotiation", 180000, 75),
            ("MediCare Speciality Centre",  "Patient-portal subscription — 12 months",      "qualified",   320000, 40),
            ("Saanvi Dental Studio",        "Smile-makeover package (Mr. Kulkarni)",        "lead",         85000, 25),
            ("Apollo Family Clinic",        "Diabetes follow-up programme — Q1 cohort",     "won",         150000, 100),
        ],
        "tasks": [
            {"title": "Call back Mr. Kulkarni about smile-makeover quote",     "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send WhatsApp reminders for tomorrow's appointments",   "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up on overdue lab payment — WellSpring",         "priority": "normal", "status": "open",        "due_offset": -3},
            {"title": "Update intake form — add insurance photo upload",       "priority": "normal", "status": "in_progress", "due_offset": 4},
            {"title": "Confirm cardiology referral — Mrs. Mehta",              "priority": "normal", "status": "open",        "due_offset": 1},
            {"title": "Renew clinic biomedical-waste contract",                "priority": "low",    "status": "open",        "due_offset": 12},
        ],
        "invoices": [
            {"customer": "Apollo Family Clinic",       "issue_offset": -14, "due_offset": +16, "status": "sent",  "line_items": [{"description": "Health-check package x 25 employees", "quantity": 25, "unit_price": 4500}], "tax_pct": 0},
            {"customer": "WellSpring Diagnostics",     "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Sample-collection software setup", "quantity": 1, "unit_price": 90000}, {"description": "Per-collection fee (Mar batch)", "quantity": 60, "unit_price": 250}], "tax_pct": 18},
            {"customer": "MediCare Speciality Centre", "issue_offset": -60, "due_offset": -30, "status": "paid",  "line_items": [{"description": "Patient-portal pilot — January", "quantity": 1, "unit_price": 60000}], "tax_pct": 18},
            {"customer": "Saanvi Dental Studio",       "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Smile-makeover (root canal + crown)", "quantity": 1, "unit_price": 35000}], "tax_pct": 18},
        ],
    },

    # ── Real estate ───────────────────────────────────────────────────────
    "Real estate": {
        "icp": (
            "Independent property brokers and small agencies in Indian metros. "
            "Decision-maker is the broker / agency owner. Sweet spot: 50-300 "
            "active listings, residential + commercial mix."
        ),
        "companies": [
            {"name": "Prestige Whitefield",  "industry": "Real estate", "size": "200-1000", "website": "prestige.example.in"},
            {"name": "Brigade Cornerstone",  "industry": "Real estate", "size": "200-1000", "website": "brigade.example.in"},
            {"name": "Sobha Indraprastha",   "industry": "Real estate", "size": "50-200",   "website": "sobha.example.in"},
            {"name": "Mantri Webcity",       "industry": "Real estate", "size": "200-1000", "website": "mantri.example.in"},
        ],
        "contacts": [
            ("Prestige Whitefield", {"first_name": "Karan",   "last_name": "Malhotra", "title": "Buyer — 3BHK",           "email": "karan.m@example.com",       "phone": "+91 90080 11001"}),
            ("Prestige Whitefield", {"first_name": "Sneha",   "last_name": "Bhat",     "title": "Buyer — 2BHK",           "email": "sneha.b@example.com",       "phone": "+91 90080 11002"}),
            ("Brigade Cornerstone", {"first_name": "Arjun",   "last_name": "Rao",      "title": "Investor — Commercial",  "email": "arjun.rao@example.com",     "phone": "+91 90080 22001"}),
            ("Sobha Indraprastha",  {"first_name": "Divya",   "last_name": "Kapoor",   "title": "First-time buyer",       "email": "divya.k@example.com",       "phone": "+91 90080 33001"}),
            ("Mantri Webcity",      {"first_name": "Vivek",   "last_name": "Joshi",    "title": "NRI investor",           "email": "vivek.j@example.com",       "phone": "+91 90080 44001"}),
        ],
        "deals": [
            ("Prestige Whitefield", "3BHK @ ₹1.6Cr — Karan Malhotra",            "negotiation", 16000000, 70),
            ("Brigade Cornerstone", "Office floor — Arjun Rao (10,000 sq.ft)",   "proposal",    35000000, 50),
            ("Sobha Indraprastha",  "2BHK @ ₹85L — Divya Kapoor",                "qualified",    8500000, 30),
            ("Mantri Webcity",      "Villa plot — Vivek Joshi (NRI)",            "lead",        12000000, 15),
            ("Prestige Whitefield", "2BHK @ ₹95L — closed deal Q1",              "won",          9500000, 100),
        ],
        "tasks": [
            {"title": "Schedule site visit — Karan (Sat 11 AM Prestige)",       "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send floor-plan PDF to Sneha (2BHK options)",            "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up — Vivek hasn't replied in 6 days",             "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Update Brigade Cornerstone brochure — new pricing",      "priority": "normal", "status": "in_progress", "due_offset": 3},
            {"title": "Call back Divya about home loan options (HDFC)",         "priority": "normal", "status": "open",        "due_offset": 1},
            {"title": "Renew RERA listing for Mantri Webcity plots",            "priority": "low",    "status": "open",        "due_offset": 14},
        ],
        "invoices": [
            {"customer": "Prestige Whitefield",  "issue_offset": -20, "due_offset": +10, "status": "sent",  "line_items": [{"description": "Brokerage — 2BHK closing (advance)", "quantity": 1, "unit_price": 47500}], "tax_pct": 18},
            {"customer": "Brigade Cornerstone",  "issue_offset": -50, "due_offset": -20, "status": "sent",  "line_items": [{"description": "Commercial brokerage advance", "quantity": 1, "unit_price": 175000}], "tax_pct": 18},
            {"customer": "Sobha Indraprastha",   "issue_offset": -90, "due_offset": -60, "status": "paid",  "line_items": [{"description": "2BHK brokerage (Q4 closing)", "quantity": 1, "unit_price": 42500}], "tax_pct": 18},
            {"customer": "Mantri Webcity",       "issue_offset":  0,  "due_offset":  15, "status": "draft", "line_items": [{"description": "Plot brokerage estimate (Vivek J.)", "quantity": 1, "unit_price": 60000}], "tax_pct": 18},
        ],
    },

    # ── Education ─────────────────────────────────────────────────────────
    "Education": {
        "icp": (
            "Coaching institutes, K-12 prep centres, and online courses (10-100 "
            "staff). Decision-maker is the founder / admissions head. Sweet spot: "
            "200-2000 students per year, strong WhatsApp parent communication."
        ),
        "companies": [
            {"name": "Sunrise Public School",    "industry": "Education", "size": "50-200",  "website": "sunrise.example.in"},
            {"name": "BrightPath Coaching",      "industry": "Education", "size": "10-50",   "website": "brightpath.example.in"},
            {"name": "ScholarMinds Tutorials",   "industry": "Education", "size": "10-50",   "website": "scholarminds.example.in"},
            {"name": "FutureSkills Academy",     "industry": "Education", "size": "50-200",  "website": "futureskills.example.in"},
        ],
        "contacts": [
            ("Sunrise Public School",   {"first_name": "Mrs.",   "last_name": "Pratima Shah",   "title": "Parent — Aarav (Grade 8)",   "email": "pratima.shah@example.com", "phone": "+91 99720 11001"}),
            ("BrightPath Coaching",     {"first_name": "Aditya", "last_name": "Verma",          "title": "JEE applicant (12th)",        "email": "aditya.v@example.com",     "phone": "+91 99720 22001"}),
            ("BrightPath Coaching",     {"first_name": "Mr.",    "last_name": "Suresh Kumar",   "title": "Parent — Riya (NEET)",        "email": "suresh.k@example.com",     "phone": "+91 99720 22002"}),
            ("ScholarMinds Tutorials",  {"first_name": "Ananya", "last_name": "Singh",          "title": "CBSE 10th student",           "email": "ananya.s@example.com",     "phone": "+91 99720 33001"}),
            ("FutureSkills Academy",    {"first_name": "Rahul",  "last_name": "Kumar",          "title": "Data-science course inquiry", "email": "rahul.k@example.com",      "phone": "+91 99720 44001"}),
        ],
        "deals": [
            ("Sunrise Public School",   "Admission — Aarav (Grade 8 transfer)",          "proposal",     85000, 55),
            ("BrightPath Coaching",     "JEE 2-year programme — Aditya Verma",           "negotiation", 145000, 75),
            ("BrightPath Coaching",     "NEET 1-year crash — Riya (Suresh's daughter)",  "qualified",    95000, 40),
            ("ScholarMinds Tutorials",  "CBSE 10th maths + science combo — Ananya",      "lead",         24000, 25),
            ("BrightPath Coaching",     "JEE foundation — Q4 batch (closed)",            "won",         110000, 100),
        ],
        "tasks": [
            {"title": "Call back Mrs. Pratima about Aarav's admission interview",   "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send fee schedule to Suresh Kumar (Riya — NEET)",            "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up — Aditya hasn't paid registration fee",            "priority": "normal", "status": "open",        "due_offset": -4},
            {"title": "Prep parent-teacher meeting agenda (Friday)",                "priority": "normal", "status": "in_progress", "due_offset": 3},
            {"title": "Update brochure — new data-science syllabus",                "priority": "normal", "status": "open",        "due_offset": 2},
            {"title": "Send WhatsApp test-result message to JEE batch",             "priority": "low",    "status": "open",        "due_offset": 7},
        ],
        "invoices": [
            {"customer": "Sunrise Public School",   "issue_offset": -10, "due_offset": +20, "status": "sent",  "line_items": [{"description": "Grade 8 admission fee — Aarav Shah", "quantity": 1, "unit_price": 45000}, {"description": "Books + uniform deposit", "quantity": 1, "unit_price": 8500}], "tax_pct": 0},
            {"customer": "BrightPath Coaching",     "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "JEE 2-year — Aditya V. (instalment 2/4)", "quantity": 1, "unit_price": 35000}], "tax_pct": 18},
            {"customer": "ScholarMinds Tutorials",  "issue_offset": -60, "due_offset": -30, "status": "paid",  "line_items": [{"description": "CBSE 10th maths — Ananya S. (term 1)", "quantity": 1, "unit_price": 12000}], "tax_pct": 18},
            {"customer": "FutureSkills Academy",    "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Data-science course — Rahul K. (estimate)", "quantity": 1, "unit_price": 28000}], "tax_pct": 18},
        ],
    },

    # ── Legal ─────────────────────────────────────────────────────────────
    "Legal": {
        "icp": (
            "Solo practitioners and small law firms (2-15 lawyers) in Indian "
            "metros. Decision-maker is the principal/founding partner. Sweet "
            "spot: corporate, property, or family-law practice with 30-100 "
            "active matters."
        ),
        "companies": [
            {"name": "Mehta & Associates",       "industry": "Legal", "size": "10-50",  "website": "mehtalaw.example.in"},
            {"name": "Krishnan Property Law",    "industry": "Legal", "size": "1-10",   "website": "kproperty.example.in"},
            {"name": "Singhania Corporate",      "industry": "Legal", "size": "50-200", "website": "singhania.example.in"},
            {"name": "Iyer Family Counsel",      "industry": "Legal", "size": "1-10",   "website": "iyerfamily.example.in"},
        ],
        "contacts": [
            ("Mehta & Associates",    {"first_name": "Mr.",     "last_name": "Rakesh Gupta",   "title": "Client — Corporate restructuring",  "email": "rakesh.g@example.com",      "phone": "+91 98180 11001"}),
            ("Krishnan Property Law", {"first_name": "Mrs.",    "last_name": "Anjali Menon",   "title": "Client — Apartment dispute",        "email": "anjali.m@example.com",      "phone": "+91 98180 22001"}),
            ("Singhania Corporate",   {"first_name": "Mr.",     "last_name": "Vinod Sharma",   "title": "GC — Tech startup",                  "email": "vinod.s@example.com",       "phone": "+91 98180 33001"}),
            ("Iyer Family Counsel",   {"first_name": "Priya",   "last_name": "Iyer",           "title": "Client — Estate planning",           "email": "priya.iyer@example.com",    "phone": "+91 98180 44001"}),
            ("Mehta & Associates",    {"first_name": "Dr.",     "last_name": "Suresh Pillai",  "title": "Client — Defamation matter",         "email": "suresh.p@example.com",      "phone": "+91 98180 11002"}),
        ],
        "deals": [
            ("Mehta & Associates",    "Corporate restructuring — Rakesh Gupta",      "proposal",    450000, 60),
            ("Krishnan Property Law", "Apartment dispute — Mrs. Menon",              "negotiation", 175000, 75),
            ("Singhania Corporate",   "Series-B closing — TechStartup (advisory)",   "qualified",   850000, 40),
            ("Iyer Family Counsel",   "Estate plan — Priya Iyer family",             "lead",        125000, 25),
            ("Mehta & Associates",    "Trademark registration (closed)",             "won",          85000, 100),
        ],
        "tasks": [
            {"title": "Draft demand notice for apartment dispute — Mrs. Menon",     "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Court appearance — Suresh Pillai defamation (Wed 11 AM)",    "priority": "high",   "status": "open",        "due_offset": 1},
            {"title": "Send retainer agreement to Vinod (Series-B advisory)",       "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Compile estate documents — Priya Iyer (will + nominee)",     "priority": "normal", "status": "in_progress", "due_offset": 5},
            {"title": "File quarterly compliance — Mehta & Associates",             "priority": "normal", "status": "open",        "due_offset": 8},
            {"title": "Renew Bar Council membership (annual)",                      "priority": "low",    "status": "open",        "due_offset": 30},
        ],
        "invoices": [
            {"customer": "Mehta & Associates",     "issue_offset": -15, "due_offset": +15, "status": "sent",  "line_items": [{"description": "Restructuring advisory — March", "quantity": 1, "unit_price": 150000}], "tax_pct": 18},
            {"customer": "Krishnan Property Law",  "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Property dispute — first hearing fee", "quantity": 1, "unit_price": 75000}], "tax_pct": 18},
            {"customer": "Singhania Corporate",    "issue_offset": -75, "due_offset": -45, "status": "paid",  "line_items": [{"description": "Series-A due diligence (closed)", "quantity": 1, "unit_price": 250000}], "tax_pct": 18},
            {"customer": "Iyer Family Counsel",    "issue_offset":  0,  "due_offset":  20, "status": "draft", "line_items": [{"description": "Estate planning — initial consult + draft", "quantity": 1, "unit_price": 50000}], "tax_pct": 18},
        ],
    },

    # ── Ecommerce ─────────────────────────────────────────────────────────
    "Ecommerce": {
        "icp": (
            "D2C brands and small online retailers selling 100-5000 SKUs via "
            "Shopify, Amazon India, Flipkart, or own website. Decision-maker "
            "is the founder / operations head. Sweet spot: ₹50L-₹5Cr GMV."
        ),
        "companies": [
            {"name": "TasteCraft Foods",     "industry": "Ecommerce", "size": "10-50",  "website": "tastecraft.example.in"},
            {"name": "Boho Threads",         "industry": "Ecommerce", "size": "10-50",  "website": "boho.example.in"},
            {"name": "NomadGear",            "industry": "Ecommerce", "size": "1-10",   "website": "nomadgear.example.in"},
            {"name": "PureSkin Naturals",    "industry": "Ecommerce", "size": "50-200", "website": "pureskin.example.in"},
        ],
        "contacts": [
            ("TasteCraft Foods",   {"first_name": "Rajesh",   "last_name": "Krishnan", "title": "Customer — bulk order",   "email": "rajesh.k@example.com",   "phone": "+91 91160 11001"}),
            ("Boho Threads",       {"first_name": "Nisha",    "last_name": "Roy",      "title": "Wholesale buyer",         "email": "nisha.r@example.com",    "phone": "+91 91160 22001"}),
            ("NomadGear",          {"first_name": "Arjun",    "last_name": "Bhalla",   "title": "Customer — return",       "email": "arjun.b@example.com",    "phone": "+91 91160 33001"}),
            ("PureSkin Naturals",  {"first_name": "Smita",    "last_name": "Desai",    "title": "Salon owner — B2B",       "email": "smita.d@example.com",    "phone": "+91 91160 44001"}),
            ("TasteCraft Foods",   {"first_name": "Karthik",  "last_name": "Reddy",    "title": "Influencer collab",       "email": "karthik.r@example.com",  "phone": "+91 91160 11002"}),
        ],
        "deals": [
            ("TasteCraft Foods",    "Corporate gift order — Diwali (250 boxes)",       "proposal",    187500, 55),
            ("Boho Threads",        "Wholesale order — Nisha (50-piece bulk)",         "negotiation",  65000, 75),
            ("PureSkin Naturals",   "Salon B2B distribution — Smita (pilot 5 salons)", "qualified",   120000, 40),
            ("NomadGear",           "Influencer collab — Karthik Reddy (3-piece)",     "lead",         18000, 25),
            ("TasteCraft Foods",    "Wedding gift order (closed)",                     "won",         145000, 100),
        ],
        "tasks": [
            {"title": "Confirm courier pickup — 250 Diwali gift boxes",             "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Reply to Arjun's return request (NomadGear order #1284)",    "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up on Boho Threads wholesale — Nisha (4 days idle)",  "priority": "normal", "status": "open",        "due_offset": -1},
            {"title": "Update Amazon listing — new pricing for top 10 SKUs",        "priority": "normal", "status": "in_progress", "due_offset": 2},
            {"title": "Send PureSkin distribution brochure to Smita",               "priority": "normal", "status": "open",        "due_offset": 1},
            {"title": "Restock alert — Boho hand-block kurtas (under 5 left)",      "priority": "low",    "status": "open",        "due_offset": 5},
        ],
        "invoices": [
            {"customer": "TasteCraft Foods",     "issue_offset": -10, "due_offset": +20, "status": "sent",  "line_items": [{"description": "Diwali gift box — Classic 6-pc", "quantity": 250, "unit_price": 750}], "tax_pct": 5},
            {"customer": "Boho Threads",         "issue_offset": -40, "due_offset": -10, "status": "sent",  "line_items": [{"description": "Hand-block kurta — wholesale", "quantity": 50, "unit_price": 1200}, {"description": "Custom embroidery — add-on", "quantity": 20, "unit_price": 250}], "tax_pct": 5},
            {"customer": "PureSkin Naturals",    "issue_offset": -75, "due_offset": -45, "status": "paid",  "line_items": [{"description": "Salon trial pack (20 SKUs x 5 salons)", "quantity": 5, "unit_price": 12000}], "tax_pct": 18},
            {"customer": "NomadGear",            "issue_offset":  0,  "due_offset":  15, "status": "draft", "line_items": [{"description": "Influencer collab — 3-piece custom", "quantity": 3, "unit_price": 5500}], "tax_pct": 18},
        ],
    },

    # ── Finance ───────────────────────────────────────────────────────────
    "Finance": {
        "icp": (
            "Chartered accountants, financial advisors, insurance brokers, and "
            "small wealth-management firms (2-20 staff). Decision-maker is the "
            "principal CA / RIA / advisor. Sweet spot: 50-500 active clients."
        ),
        "companies": [
            {"name": "Patel & Co. Chartered Accountants", "industry": "Finance", "size": "10-50", "website": "patelca.example.in"},
            {"name": "Shenoy Wealth Advisors",            "industry": "Finance", "size": "1-10",  "website": "shenoywealth.example.in"},
            {"name": "Bhat Insurance Brokers",            "industry": "Finance", "size": "10-50", "website": "bhatinsurance.example.in"},
            {"name": "Anand Tax Consultancy",             "industry": "Finance", "size": "1-10",  "website": "anandtax.example.in"},
        ],
        "contacts": [
            ("Patel & Co. Chartered Accountants", {"first_name": "Mr.",   "last_name": "Vijay Mehta",       "title": "Client — GST + IT filing",        "email": "vijay.m@example.com",     "phone": "+91 96770 11001"}),
            ("Shenoy Wealth Advisors",            {"first_name": "Mrs.",  "last_name": "Lakshmi Krishnan",  "title": "Client — retirement planning",    "email": "lakshmi.k@example.com",   "phone": "+91 96770 22001"}),
            ("Bhat Insurance Brokers",            {"first_name": "Mr.",   "last_name": "Pradeep Kumar",     "title": "Term-life applicant (₹2Cr)",      "email": "pradeep.k@example.com",   "phone": "+91 96770 33001"}),
            ("Anand Tax Consultancy",             {"first_name": "Smt.",  "last_name": "Sushila Rao",       "title": "Client — capital gains",          "email": "sushila.r@example.com",   "phone": "+91 96770 44001"}),
            ("Patel & Co. Chartered Accountants", {"first_name": "Mr.",   "last_name": "Karan Shah",        "title": "New client — startup audit",      "email": "karan.s@example.com",     "phone": "+91 96770 11002"}),
        ],
        "deals": [
            ("Patel & Co. Chartered Accountants", "Annual retainer — Vijay Mehta (GST + IT)",      "proposal",     85000, 60),
            ("Shenoy Wealth Advisors",            "Portfolio review + plan — Mrs. Krishnan",        "negotiation",  60000, 75),
            ("Bhat Insurance Brokers",            "Term-life ₹2Cr — Pradeep Kumar",                 "qualified",    45000, 40),
            ("Anand Tax Consultancy",             "Capital-gains advisory — Smt. Rao (FY return)",  "lead",         22000, 25),
            ("Patel & Co. Chartered Accountants", "Startup audit Q1 (closed)",                      "won",         125000, 100),
        ],
        "tasks": [
            {"title": "Send GST-3B reminder to Vijay Mehta (due in 5 days)",        "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Schedule portfolio review call — Mrs. Krishnan (Sat)",       "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up on overdue retainer invoice — Karan Shah",         "priority": "normal", "status": "open",        "due_offset": -3},
            {"title": "Compile capital-gains worksheet — Smt. Rao FY return",       "priority": "normal", "status": "in_progress", "due_offset": 4},
            {"title": "Confirm medical underwriting for Pradeep's term-life",      "priority": "normal", "status": "open",        "due_offset": 2},
            {"title": "Renew ICAI membership (annual)",                             "priority": "low",    "status": "open",        "due_offset": 20},
        ],
        "invoices": [
            {"customer": "Patel & Co. Chartered Accountants", "issue_offset": -12, "due_offset": +18, "status": "sent",  "line_items": [{"description": "GST-3B + GSTR-1 filing — March", "quantity": 1, "unit_price": 12500}], "tax_pct": 18},
            {"customer": "Shenoy Wealth Advisors",            "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Quarterly portfolio review — Q4", "quantity": 1, "unit_price": 35000}], "tax_pct": 18},
            {"customer": "Anand Tax Consultancy",             "issue_offset": -80, "due_offset": -50, "status": "paid",  "line_items": [{"description": "IT return filing — Smt. Rao (FY23)", "quantity": 1, "unit_price": 8500}], "tax_pct": 18},
            {"customer": "Bhat Insurance Brokers",            "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Term-life ₹2Cr — first-year premium est.", "quantity": 1, "unit_price": 24500}], "tax_pct": 18},
        ],
    },

    # ── SaaS ──────────────────────────────────────────────────────────────
    "SaaS": {
        "icp": (
            "Indian B2B SaaS founders selling ₹2k-₹50k/month products to mid-"
            "market customers. 2-30 staff. Decision-makers are founder + head "
            "of sales / customer success."
        ),
        "companies": [
            {"name": "CloudOps India",   "industry": "Technology", "size": "50-200",  "website": "cloudopsindia.example.in"},
            {"name": "Nimbus Analytics", "industry": "Technology", "size": "200-1000","website": "nimbus.example.in"},
            {"name": "ScribeAI",         "industry": "Technology", "size": "10-50",   "website": "scribe.example.in"},
            {"name": "MeshLogistics",    "industry": "Logistics",  "size": "50-200",  "website": "mesh.example.in"},
        ],
        "contacts": [
            ("CloudOps India",    {"first_name": "Anand",  "last_name": "Subramanian", "title": "CTO — pilot evaluator",        "email": "anand.s@example.com",   "phone": "+91 93840 11001"}),
            ("Nimbus Analytics",  {"first_name": "Meera",  "last_name": "Pillai",      "title": "VP Engineering",                "email": "meera.p@example.com",   "phone": "+91 93840 22001"}),
            ("ScribeAI",          {"first_name": "Karan",  "last_name": "Shetty",      "title": "Founder — competitor demo",      "email": "karan.s@example.com",   "phone": "+91 93840 33001"}),
            ("MeshLogistics",     {"first_name": "Divya",  "last_name": "Khanna",      "title": "Head of Ops",                   "email": "divya.k@example.com",   "phone": "+91 93840 44001"}),
            ("CloudOps India",    {"first_name": "Rohit",  "last_name": "Gupta",       "title": "Engineering manager (champion)", "email": "rohit.g@example.com",   "phone": "+91 93840 11002"}),
        ],
        "deals": [
            ("CloudOps India",    "Annual contract — 25 seats (CloudOps pilot)",    "proposal",    450000, 60),
            ("Nimbus Analytics",  "Enterprise rollout — 100 seats",                 "negotiation", 1800000, 80),
            ("ScribeAI",          "Annual contract — 10 seats (mid-market)",        "qualified",   180000, 40),
            ("MeshLogistics",     "Pilot — 5 seats (3-month POC)",                  "lead",         45000, 25),
            ("CloudOps India",    "Self-serve → Pro upgrade — Q1",                  "won",          85000, 100),
        ],
        "tasks": [
            {"title": "Send security questionnaire response — Nimbus VP Eng",       "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Demo call with Karan Shetty (ScribeAI — Tue 4 PM)",          "priority": "high",   "status": "open",        "due_offset": 1},
            {"title": "Follow up — Anand hasn't responded since pricing sent",      "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Draft renewal proposal — MeshLogistics (Q1 expiring)",       "priority": "normal", "status": "in_progress", "due_offset": 5},
            {"title": "Schedule POC kickoff call — Divya Khanna",                   "priority": "normal", "status": "open",        "due_offset": 2},
            {"title": "Review usage analytics dashboard for churn signals",         "priority": "low",    "status": "open",        "due_offset": 7},
        ],
        "invoices": [
            {"customer": "CloudOps India",   "issue_offset": -15, "due_offset": +15, "status": "sent",  "line_items": [{"description": "Annual subscription — 25 seats x ₹1,200/mo", "quantity": 12, "unit_price": 30000}], "tax_pct": 18},
            {"customer": "Nimbus Analytics", "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Annual subscription — 100 seats (Y1)", "quantity": 1, "unit_price": 1500000}], "tax_pct": 18},
            {"customer": "ScribeAI",         "issue_offset": -90, "due_offset": -60, "status": "paid",  "line_items": [{"description": "Mid-market plan — 10 seats (Q4)", "quantity": 3, "unit_price": 15000}], "tax_pct": 18},
            {"customer": "MeshLogistics",    "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Pilot — 3-month POC (5 seats)", "quantity": 1, "unit_price": 45000}], "tax_pct": 18},
        ],
    },

    # ── Manufacturing ─────────────────────────────────────────────────────
    "Manufacturing": {
        "icp": (
            "Small manufacturing units (20-200 workers) in metal fabrication, "
            "auto parts, textiles, or food processing. Decision-maker is the "
            "owner / plant manager. Sweet spot: ₹2Cr-₹20Cr turnover."
        ),
        "companies": [
            {"name": "Sterling Auto Parts",    "industry": "Manufacturing", "size": "50-200",  "website": "sterling.example.in"},
            {"name": "PrecisionMet Engineering","industry": "Manufacturing","size": "10-50",   "website": "precisionmet.example.in"},
            {"name": "Krishna Textiles",       "industry": "Manufacturing", "size": "200-1000","website": "krishnatex.example.in"},
            {"name": "Nandi Food Processing",  "industry": "Manufacturing", "size": "50-200",  "website": "nandifood.example.in"},
        ],
        "contacts": [
            ("Sterling Auto Parts",     {"first_name": "Mr.", "last_name": "Bharat Patel",   "title": "Plant Manager",        "email": "bharat.p@example.com",   "phone": "+91 94250 11001"}),
            ("PrecisionMet Engineering",{"first_name": "Mr.", "last_name": "Sanjay Kulkarni","title": "Owner",                "email": "sanjay.k@example.com",   "phone": "+91 94250 22001"}),
            ("Krishna Textiles",        {"first_name": "Mr.", "last_name": "Ramesh Babu",    "title": "Purchase Head",        "email": "ramesh.b@example.com",   "phone": "+91 94250 33001"}),
            ("Nandi Food Processing",   {"first_name": "Mrs.","last_name": "Geeta Hegde",    "title": "Founder",              "email": "geeta.h@example.com",    "phone": "+91 94250 44001"}),
            ("Sterling Auto Parts",     {"first_name": "Mr.", "last_name": "Suresh Naik",    "title": "Quality manager",      "email": "suresh.n@example.com",   "phone": "+91 94250 11002"}),
        ],
        "deals": [
            ("Sterling Auto Parts",     "Annual contract — brake-pad supply (PO#2024-87)",   "proposal",     875000, 60),
            ("PrecisionMet Engineering","CNC parts — bulk order (auto-industry)",            "negotiation", 1250000, 75),
            ("Krishna Textiles",        "Cotton yarn supply — 6-month contract",             "qualified",    560000, 40),
            ("Nandi Food Processing",   "Pickle export packaging — sample order",            "lead",         185000, 25),
            ("Sterling Auto Parts",     "Q1 brake-pad delivery (closed)",                     "won",         650000, 100),
        ],
        "tasks": [
            {"title": "Send revised quote — Sterling annual contract (lower margin)",        "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Schedule plant visit — Sanjay (PrecisionMet) Thursday",                "priority": "high",   "status": "open",        "due_offset": 2},
            {"title": "Follow up on overdue payment — Krishna Textiles (₹2.4L)",              "priority": "normal", "status": "open",        "due_offset": -5},
            {"title": "Send packaging spec sheet to Geeta (Nandi pickle export)",             "priority": "normal", "status": "in_progress", "due_offset": 3},
            {"title": "Renew GST registration certificate",                                    "priority": "normal", "status": "open",        "due_offset": 10},
            {"title": "Update vendor onboarding docs — new buyers in Q2",                     "priority": "low",    "status": "open",        "due_offset": 14},
        ],
        "invoices": [
            {"customer": "Sterling Auto Parts",      "issue_offset": -20, "due_offset": +10, "status": "sent",  "line_items": [{"description": "Brake pads — Q1 batch (5000 units)", "quantity": 5000, "unit_price": 125}], "tax_pct": 18},
            {"customer": "PrecisionMet Engineering", "issue_offset": -50, "due_offset": -20, "status": "sent",  "line_items": [{"description": "CNC machined parts — 250 units", "quantity": 250, "unit_price": 1850}], "tax_pct": 18},
            {"customer": "Krishna Textiles",         "issue_offset": -90, "due_offset": -60, "status": "paid",  "line_items": [{"description": "Cotton yarn — bulk supply (5 tonnes)", "quantity": 5, "unit_price": 95000}], "tax_pct": 5},
            {"customer": "Nandi Food Processing",    "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Pickle export packaging — sample batch", "quantity": 1, "unit_price": 28500}], "tax_pct": 18},
        ],
    },

    # ── Hospitality ───────────────────────────────────────────────────────
    "Hospitality": {
        "icp": (
            "Boutique hotels, restaurants, cafes, event venues, and resorts "
            "(10-100 staff). Decision-makers are owner / GM. Sweet spot: 20-60 "
            "rooms / 50-200 covers / strong WhatsApp guest comms."
        ),
        "companies": [
            {"name": "Coorg Hilltop Stays",   "industry": "Hospitality", "size": "10-50",  "website": "coorghilltop.example.in"},
            {"name": "Tide & Tide Beach Cafe","industry": "Hospitality", "size": "10-50",  "website": "tide.example.in"},
            {"name": "Maharaja Banquet Hall", "industry": "Hospitality", "size": "10-50",  "website": "maharaja.example.in"},
            {"name": "Spice Route Bistro",    "industry": "Hospitality", "size": "1-10",   "website": "spice.example.in"},
        ],
        "contacts": [
            ("Coorg Hilltop Stays",     {"first_name": "Mr.",   "last_name": "Vikram Singh",     "title": "Guest — 3-night stay",         "email": "vikram.s@example.com",   "phone": "+91 99860 11001"}),
            ("Tide & Tide Beach Cafe",  {"first_name": "Ms.",   "last_name": "Anushka Joshi",    "title": "Birthday-party booking",        "email": "anushka.j@example.com",  "phone": "+91 99860 22001"}),
            ("Maharaja Banquet Hall",   {"first_name": "Mr.",   "last_name": "Hari Krishnan",    "title": "Wedding inquiry — 350 pax",     "email": "hari.k@example.com",     "phone": "+91 99860 33001"}),
            ("Spice Route Bistro",      {"first_name": "Mrs.",  "last_name": "Sunita Rajan",     "title": "Corporate dinner — 40 pax",     "email": "sunita.r@example.com",   "phone": "+91 99860 44001"}),
            ("Coorg Hilltop Stays",     {"first_name": "Mr.",   "last_name": "Aditya Verma",     "title": "Returning guest — anniv.",      "email": "aditya.v@example.com",   "phone": "+91 99860 11002"}),
        ],
        "deals": [
            ("Coorg Hilltop Stays",     "3-night stay — Vikram (deluxe room x2)",        "proposal",     45000, 60),
            ("Maharaja Banquet Hall",   "Wedding — Hari Krishnan family (350 pax)",       "negotiation", 850000, 75),
            ("Tide & Tide Beach Cafe",  "Birthday booking — Anushka (20-25 guests)",      "qualified",    18000, 50),
            ("Spice Route Bistro",      "Corporate dinner — Sunita (40 pax)",             "lead",         32000, 25),
            ("Coorg Hilltop Stays",     "Anniversary package (closed)",                   "won",          28000, 100),
        ],
        "tasks": [
            {"title": "Confirm room availability for Vikram (Coorg, Sat-Mon)",       "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send wedding menu to Hari Krishnan (Maharaja, 350 pax)",       "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up — Anushka birthday booking (cake confirmation)",     "priority": "normal", "status": "open",        "due_offset": -1},
            {"title": "Prep corporate dinner spec — Sunita (vegan + jain options)",   "priority": "normal", "status": "in_progress", "due_offset": 3},
            {"title": "Send anniversary check-in WhatsApp to returning guest",        "priority": "normal", "status": "open",        "due_offset": 1},
            {"title": "Review Tripadvisor reviews from last weekend",                 "priority": "low",    "status": "open",        "due_offset": 4},
        ],
        "invoices": [
            {"customer": "Coorg Hilltop Stays",     "issue_offset": -8,  "due_offset": +12, "status": "sent",  "line_items": [{"description": "Deluxe room x 2 (3 nights)", "quantity": 6, "unit_price": 6500}, {"description": "Meal plan", "quantity": 6, "unit_price": 1200}], "tax_pct": 12},
            {"customer": "Maharaja Banquet Hall",   "issue_offset": -30, "due_offset": -5,  "status": "sent",  "line_items": [{"description": "Wedding venue deposit (refundable)", "quantity": 1, "unit_price": 250000}], "tax_pct": 18},
            {"customer": "Spice Route Bistro",      "issue_offset": -60, "due_offset": -30, "status": "paid",  "line_items": [{"description": "Corporate lunch — 30 pax", "quantity": 30, "unit_price": 850}], "tax_pct": 5},
            {"customer": "Tide & Tide Beach Cafe",  "issue_offset":  0,  "due_offset":  10, "status": "draft", "line_items": [{"description": "Birthday booking estimate — 25 pax incl. cake", "quantity": 1, "unit_price": 18000}], "tax_pct": 5},
        ],
    },

    # ── Local services ────────────────────────────────────────────────────
    "Local services": {
        "icp": (
            "Local service businesses — electricians, plumbers, AC repair, "
            "carpenters, pest control, home cleaning (1-10 staff). Decision-"
            "maker is the owner. Strongest channel: WhatsApp + local reviews."
        ),
        "companies": [
            {"name": "Ramesh Electricals",      "industry": "Local services", "size": "1-10",  "website": ""},
            {"name": "Kumar AC Repair",         "industry": "Local services", "size": "1-10",  "website": ""},
            {"name": "ProClean Home Services",  "industry": "Local services", "size": "10-50", "website": "proclean.example.in"},
            {"name": "FixIt Plumbing",          "industry": "Local services", "size": "1-10",  "website": ""},
        ],
        "contacts": [
            ("Ramesh Electricals",     {"first_name": "Mrs.",  "last_name": "Anita Sharma",    "title": "Customer — wiring repair",    "email": "anita.s@example.com",     "phone": "+91 98860 11001"}),
            ("Kumar AC Repair",        {"first_name": "Mr.",   "last_name": "Raghav Iyer",     "title": "Customer — annual service",    "email": "raghav.i@example.com",    "phone": "+91 98860 22001"}),
            ("ProClean Home Services", {"first_name": "Ms.",   "last_name": "Priya Reddy",     "title": "Customer — deep clean",        "email": "priya.r@example.com",     "phone": "+91 98860 33001"}),
            ("FixIt Plumbing",         {"first_name": "Mr.",   "last_name": "Suresh Naidu",    "title": "Customer — bathroom leak",     "email": "suresh.n@example.com",    "phone": "+91 98860 44001"}),
            ("ProClean Home Services", {"first_name": "Mr.",   "last_name": "Karan Bhatia",    "title": "Customer — monthly cleaning",  "email": "karan.b@example.com",     "phone": "+91 98860 33002"}),
        ],
        "deals": [
            ("Ramesh Electricals",       "Full house wiring — Mrs. Sharma (3BHK)",         "proposal",     32000, 60),
            ("Kumar AC Repair",          "Annual maintenance — 4 ACs (Raghav)",            "negotiation",   8800, 80),
            ("ProClean Home Services",   "Quarterly deep-clean contract — Priya",          "qualified",    12000, 40),
            ("FixIt Plumbing",           "Bathroom leak fix — Suresh Naidu",               "lead",          4500, 50),
            ("ProClean Home Services",   "Monthly clean — Karan (closed Q4)",              "won",           7800, 100),
        ],
        "tasks": [
            {"title": "Send technician to Mrs. Sharma's place — wiring inspection (10 AM)",  "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Confirm AC service slots with Raghav (4 ACs, weekend)",                "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up on Priya's deep-clean quote (3 days idle)",                  "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Schedule plumber for Suresh's leak (Mon morning)",                     "priority": "normal", "status": "in_progress", "due_offset": 1},
            {"title": "Send monthly cleaning reminder WhatsApp — Karan",                      "priority": "normal", "status": "open",        "due_offset": 3},
            {"title": "Restock AC service kit (filters running low)",                         "priority": "low",    "status": "open",        "due_offset": 5},
        ],
        "invoices": [
            {"customer": "Ramesh Electricals",      "issue_offset": -5,  "due_offset": +15, "status": "sent",  "line_items": [{"description": "Wiring inspection + minor repair", "quantity": 1, "unit_price": 1800}], "tax_pct": 18},
            {"customer": "Kumar AC Repair",         "issue_offset": -30, "due_offset": -5,  "status": "sent",  "line_items": [{"description": "AC annual service — split (1.5T)", "quantity": 4, "unit_price": 1200}], "tax_pct": 18},
            {"customer": "ProClean Home Services",  "issue_offset": -55, "due_offset": -25, "status": "paid",  "line_items": [{"description": "Monthly cleaning — Karan Bhatia (Feb)", "quantity": 1, "unit_price": 7800}], "tax_pct": 18},
            {"customer": "FixIt Plumbing",          "issue_offset":  0,  "due_offset":  7,  "status": "draft", "line_items": [{"description": "Bathroom leak fix — Suresh Naidu (est.)", "quantity": 1, "unit_price": 4500}], "tax_pct": 18},
        ],
    },

    # ── Tutoring / coaching ───────────────────────────────────────────────
    "Tutoring / coaching": {
        "icp": "Independent tutors, coaching centres, JEE/NEET/IELTS prep, music/dance classes (1-15 staff). 50-500 students. Strong parent WhatsApp comms.",
        "companies": [
            {"name": "BrightFutures JEE Coaching", "industry": "Tutoring", "size": "10-50", "website": ""},
            {"name": "ScholarHub Tutorials",       "industry": "Tutoring", "size": "1-10",  "website": ""},
            {"name": "Saraswati Music School",     "industry": "Tutoring", "size": "1-10",  "website": ""},
            {"name": "IELTS Edge Academy",         "industry": "Tutoring", "size": "10-50", "website": ""},
        ],
        "contacts": [
            ("BrightFutures JEE Coaching", {"first_name": "Mrs.", "last_name": "Lakshmi Iyer",   "title": "Parent — Aarush (12th)",   "email": "lakshmi.i@example.com", "phone": "+91 94800 11001"}),
            ("BrightFutures JEE Coaching", {"first_name": "Aarush","last_name": "Iyer",          "title": "JEE Main 2025",            "email": "aarush.i@example.com",  "phone": "+91 94800 11002"}),
            ("ScholarHub Tutorials",       {"first_name": "Mr.",  "last_name": "Suresh Babu",   "title": "Parent — Diya (CBSE 10th)","email": "suresh.b@example.com",  "phone": "+91 94800 22001"}),
            ("Saraswati Music School",     {"first_name": "Mrs.", "last_name": "Anita Reddy",   "title": "Parent — Rhea (vocal)",    "email": "anita.r@example.com",   "phone": "+91 94800 33001"}),
            ("IELTS Edge Academy",         {"first_name": "Karan","last_name": "Mehta",          "title": "IELTS aspirant (UK)",      "email": "karan.m@example.com",   "phone": "+91 94800 44001"}),
        ],
        "deals": [
            ("BrightFutures JEE Coaching", "JEE 2-year programme — Aarush Iyer",   "proposal",   145000, 70),
            ("ScholarHub Tutorials",       "CBSE 10th tuition (term 1) — Diya",    "negotiation", 24000, 80),
            ("Saraswati Music School",     "Vocal trimester — Rhea",                "qualified",   18000, 40),
            ("IELTS Edge Academy",         "IELTS 8-week intensive — Karan",        "lead",        32000, 25),
            ("BrightFutures JEE Coaching", "JEE foundation Q4 batch (closed)",      "won",        110000, 100),
        ],
        "tasks": [
            {"title": "Schedule Aarush's parent meeting — Sat 5 PM",       "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up — Karan's IELTS payment (3 days idle)",   "priority": "high",   "status": "open",        "due_offset": -3},
            {"title": "Send recordings of last 3 vocal classes to Rhea",   "priority": "normal", "status": "in_progress", "due_offset": 1},
            {"title": "Prep weekly mock test — JEE batch",                  "priority": "normal", "status": "open",        "due_offset": 3},
            {"title": "Update brochure with new IELTS pass-rate stats",    "priority": "low",    "status": "open",        "due_offset": 7},
        ],
        "invoices": [
            {"customer": "BrightFutures JEE Coaching", "issue_offset": -10, "due_offset": +20, "status": "sent",  "line_items": [{"description": "JEE — instalment 2 (Aarush Iyer)", "quantity": 1, "unit_price": 35000}], "tax_pct": 18},
            {"customer": "ScholarHub Tutorials",       "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "CBSE 10th tuition (term 1)", "quantity": 1, "unit_price": 12000}], "tax_pct": 18},
            {"customer": "Saraswati Music School",     "issue_offset": -60, "due_offset": -30, "status": "paid",  "line_items": [{"description": "Vocal trimester — Rhea (paid)", "quantity": 1, "unit_price": 18000}], "tax_pct": 18},
            {"customer": "IELTS Edge Academy",         "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "IELTS 8-week — Karan (estimate)", "quantity": 1, "unit_price": 32000}], "tax_pct": 18},
        ],
    },

    # ── Restaurant / cafe ─────────────────────────────────────────────────
    "Restaurant / cafe": {
        "icp": "Boutique restaurants, cafes, dhaabas (5-50 staff). 50-300 covers. Active on WhatsApp + Zomato.",
        "companies": [
            {"name": "Aroma Hyderabadi Biryani",  "industry": "Restaurant", "size": "10-50", "website": ""},
            {"name": "Cafe Mocha (Indiranagar)",  "industry": "Restaurant", "size": "10-50", "website": ""},
            {"name": "Spice Junction Multi-cuisine","industry": "Restaurant","size": "10-50","website": ""},
            {"name": "Sweet Bites Bakery + Cafe", "industry": "Restaurant", "size": "1-10",  "website": ""},
        ],
        "contacts": [
            ("Aroma Hyderabadi Biryani", {"first_name": "Mr.",  "last_name": "Naveen Kumar",   "title": "Birthday party booking — 40 pax", "email": "naveen.k@example.com",  "phone": "+91 94670 11001"}),
            ("Cafe Mocha (Indiranagar)", {"first_name": "Ms.",  "last_name": "Priya Shetty",   "title": "Anniversary table — 2",          "email": "priya.s@example.com",   "phone": "+91 94670 22001"}),
            ("Spice Junction Multi-cuisine", {"first_name": "Mr.", "last_name": "Raghav Bose", "title": "Corporate lunch — 60 pax",       "email": "raghav.b@example.com",  "phone": "+91 94670 33001"}),
            ("Sweet Bites Bakery + Cafe", {"first_name": "Mrs.","last_name": "Anjali Joshi",  "title": "Wedding cake order (5 kg)",       "email": "anjali.j@example.com",  "phone": "+91 94670 44001"}),
            ("Aroma Hyderabadi Biryani",  {"first_name": "Mr.","last_name": "Arvind Pillai",   "title": "Bulk Diwali catering — 200 pax",  "email": "arvind.p@example.com",  "phone": "+91 94670 11002"}),
        ],
        "deals": [
            ("Aroma Hyderabadi Biryani",      "Diwali catering — 200 pax (Arvind P.)",     "negotiation", 180000, 75),
            ("Spice Junction Multi-cuisine",  "Corporate lunch — 60 pax (Raghav B.)",      "proposal",     45000, 60),
            ("Aroma Hyderabadi Biryani",      "Birthday party — 40 pax (Naveen K.)",       "qualified",    32000, 50),
            ("Sweet Bites Bakery + Cafe",     "5-kg wedding cake — Anjali J.",             "lead",         12000, 30),
            ("Cafe Mocha (Indiranagar)",      "Valentines Day live music event (closed)",  "won",          45000, 100),
        ],
        "tasks": [
            {"title": "Confirm menu with Arvind for Diwali catering (200 pax)",   "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send anniversary table layout to Priya (window seat)",      "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up — Anjali's wedding cake design approval",          "priority": "normal", "status": "open",        "due_offset": -1},
            {"title": "Prep corporate lunch spec — Raghav (jain + vegan options)", "priority": "normal", "status": "in_progress", "due_offset": 2},
            {"title": "Review Zomato + Google reviews from last weekend",          "priority": "low",    "status": "open",        "due_offset": 5},
        ],
        "invoices": [
            {"customer": "Aroma Hyderabadi Biryani",  "issue_offset": -7,  "due_offset": +13, "status": "sent",  "line_items": [{"description": "Birthday party advance — 50% of 32k", "quantity": 1, "unit_price": 16000}], "tax_pct": 5},
            {"customer": "Spice Junction Multi-cuisine", "issue_offset": -30, "due_offset": -5, "status": "sent", "line_items": [{"description": "Corporate lunch — 50 pax", "quantity": 50, "unit_price": 850}], "tax_pct": 5},
            {"customer": "Cafe Mocha (Indiranagar)",  "issue_offset": -60, "due_offset": -30, "status": "paid", "line_items": [{"description": "Valentines Day live music event", "quantity": 1, "unit_price": 45000}], "tax_pct": 18},
            {"customer": "Sweet Bites Bakery + Cafe", "issue_offset":  0,  "due_offset":  10, "status": "draft","line_items": [{"description": "5-kg wedding cake (custom design)", "quantity": 1, "unit_price": 12000}], "tax_pct": 5},
        ],
    },

    # ── Beauty / salon / wellness ─────────────────────────────────────────
    "Beauty / salon / wellness": {
        "icp": "Hair salons, beauty parlours, spa + wellness centres (3-25 staff). 50-300 regular customers. WhatsApp + Instagram driven.",
        "companies": [
            {"name": "GlowUp Salon (Koramangala)", "industry": "Beauty", "size": "1-10",  "website": ""},
            {"name": "Serenity Spa & Wellness",    "industry": "Beauty", "size": "10-50", "website": ""},
            {"name": "Mehndi Studio by Pooja",     "industry": "Beauty", "size": "1-10",  "website": ""},
            {"name": "Mirror Mirror Hair Lounge",  "industry": "Beauty", "size": "10-50", "website": ""},
        ],
        "contacts": [
            ("GlowUp Salon (Koramangala)", {"first_name": "Ms.",  "last_name": "Sneha Kapoor",  "title": "Regular — colour + cut",        "email": "sneha.k@example.com",  "phone": "+91 94290 11001"}),
            ("Serenity Spa & Wellness",    {"first_name": "Mrs.", "last_name": "Anika Reddy",   "title": "Couples spa — anniv.",          "email": "anika.r@example.com",  "phone": "+91 94290 22001"}),
            ("Mehndi Studio by Pooja",     {"first_name": "Ms.",  "last_name": "Riya Sharma",   "title": "Bridal mehndi — wedding",       "email": "riya.s@example.com",   "phone": "+91 94290 33001"}),
            ("Mirror Mirror Hair Lounge",  {"first_name": "Mr.",  "last_name": "Aditya Iyer",   "title": "Bridegroom trial — Nov",        "email": "aditya.i@example.com", "phone": "+91 94290 44001"}),
            ("GlowUp Salon (Koramangala)", {"first_name": "Ms.",  "last_name": "Divya Pillai",  "title": "First-time customer",           "email": "divya.p@example.com",  "phone": "+91 94290 11002"}),
        ],
        "deals": [
            ("Mehndi Studio by Pooja",     "Bridal mehndi package (Riya S.)",              "negotiation", 28000, 80),
            ("Serenity Spa & Wellness",    "Couples anniversary spa — Anika",              "proposal",    12000, 70),
            ("Mirror Mirror Hair Lounge",  "Bridegroom hair + grooming trial — Aditya",    "qualified",   8500,  50),
            ("GlowUp Salon (Koramangala)", "Annual hair-care subscription — Divya",        "lead",        18000, 25),
            ("Mehndi Studio by Pooja",     "Reception mehndi (closed)",                     "won",         15000, 100),
        ],
        "tasks": [
            {"title": "Confirm Riya's bridal mehndi date (15 Nov) + advance",  "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send couples spa package details to Anika",              "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up — Aditya hasn't booked trial slot yet",        "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Restock hair colour kit — running low on shade 4N",      "priority": "normal", "status": "in_progress", "due_offset": 2},
            {"title": "Post before/after pics from last weekend on Instagram", "priority": "low",    "status": "open",        "due_offset": 1},
        ],
        "invoices": [
            {"customer": "Mehndi Studio by Pooja",     "issue_offset": -5,  "due_offset": +15, "status": "sent",  "line_items": [{"description": "Bridal mehndi advance (50%)", "quantity": 1, "unit_price": 14000}], "tax_pct": 18},
            {"customer": "Serenity Spa & Wellness",    "issue_offset": -35, "due_offset": -5,  "status": "sent",  "line_items": [{"description": "Couples spa package (90 min)", "quantity": 1, "unit_price": 8500}], "tax_pct": 18},
            {"customer": "GlowUp Salon (Koramangala)", "issue_offset": -60, "due_offset": -30, "status": "paid",  "line_items": [{"description": "Hair colour + cut + treatment", "quantity": 1, "unit_price": 3800}], "tax_pct": 18},
            {"customer": "Mirror Mirror Hair Lounge",  "issue_offset":  0,  "due_offset":  10, "status": "draft", "line_items": [{"description": "Bridegroom grooming trial pack", "quantity": 1, "unit_price": 8500}], "tax_pct": 18},
        ],
    },

    # ── Garment / textile retail ──────────────────────────────────────────
    "Garment / textile retail": {
        "icp": "Garment retailers + wholesalers (5-50 staff). 100-3000 SKUs. Mix of walk-in + WhatsApp catalog + B2B wholesale.",
        "companies": [
            {"name": "Rajwadi Sarees",           "industry": "Textile", "size": "10-50", "website": ""},
            {"name": "Urban Threads (kurtis)",   "industry": "Textile", "size": "10-50", "website": ""},
            {"name": "Maharani Bridal Couture",  "industry": "Textile", "size": "1-10",  "website": ""},
            {"name": "Cotton King Wholesale",    "industry": "Textile", "size": "50-200","website": ""},
        ],
        "contacts": [
            ("Rajwadi Sarees",          {"first_name": "Mrs.", "last_name": "Smita Mehra",   "title": "Wedding shopping",       "email": "smita.m@example.com", "phone": "+91 93470 11001"}),
            ("Urban Threads (kurtis)",  {"first_name": "Ms.",  "last_name": "Aanya Kapoor",  "title": "Bulk corporate order",   "email": "aanya.k@example.com", "phone": "+91 93470 22001"}),
            ("Maharani Bridal Couture", {"first_name": "Ms.",  "last_name": "Pooja Iyer",    "title": "Bridal lehenga (Dec)",   "email": "pooja.i@example.com", "phone": "+91 93470 33001"}),
            ("Cotton King Wholesale",   {"first_name": "Mr.",  "last_name": "Rajesh Joshi",  "title": "Retailer buyer",         "email": "rajesh.j@example.com","phone": "+91 93470 44001"}),
            ("Rajwadi Sarees",          {"first_name": "Mrs.", "last_name": "Lakshmi Bhat",  "title": "Loyalty regular",        "email": "lakshmi.b@example.com","phone": "+91 93470 11002"}),
        ],
        "deals": [
            ("Maharani Bridal Couture", "Bridal lehenga custom-stitched — Pooja",      "negotiation", 85000, 75),
            ("Cotton King Wholesale",   "Bulk retailer order — Rajesh (500 pieces)",   "proposal",   285000, 60),
            ("Urban Threads (kurtis)",  "Corporate kurta order — 80 pieces (Aanya)",   "qualified",   72000, 40),
            ("Rajwadi Sarees",          "Wedding trousseau shopping — Smita",          "lead",        45000, 25),
            ("Rajwadi Sarees",          "Diwali collection sale — Lakshmi (closed)",   "won",         28000, 100),
        ],
        "tasks": [
            {"title": "Send measurement appointment options to Pooja (bridal)",    "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Confirm wholesale dispatch date with Rajesh (500-piece)",   "priority": "high",   "status": "open",        "due_offset": 1},
            {"title": "Follow up on overdue retailer payment — Cotton King (₹1.2L)", "priority": "normal", "status": "open",      "due_offset": -4},
            {"title": "Send Aanya's corporate kurta design samples (3 colours)",   "priority": "normal", "status": "in_progress", "due_offset": 2},
            {"title": "Restock Banarasi silk sarees (top sellers running low)",    "priority": "low",    "status": "open",        "due_offset": 5},
        ],
        "invoices": [
            {"customer": "Maharani Bridal Couture", "issue_offset": -10, "due_offset": +20, "status": "sent",  "line_items": [{"description": "Bridal lehenga advance (50%)", "quantity": 1, "unit_price": 42500}], "tax_pct": 5},
            {"customer": "Cotton King Wholesale",   "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Cotton kurtas — wholesale 200 pcs", "quantity": 200, "unit_price": 450}], "tax_pct": 5},
            {"customer": "Urban Threads (kurtis)",  "issue_offset": -75, "due_offset": -45, "status": "paid",  "line_items": [{"description": "Corporate kurta order (60 pcs)", "quantity": 60, "unit_price": 950}], "tax_pct": 5},
            {"customer": "Rajwadi Sarees",          "issue_offset":  0,  "due_offset":  15, "status": "draft", "line_items": [{"description": "Wedding trousseau estimate (Smita M.)", "quantity": 1, "unit_price": 45000}], "tax_pct": 5},
        ],
    },

    # ── Logistics / transport ─────────────────────────────────────────────
    "Logistics / transport": {
        "icp": "Small fleet operators + freight agents (5-100 staff). 5-50 trucks. Multi-city routes, GST e-way compliance.",
        "companies": [
            {"name": "Speed Cargo Movers",       "industry": "Logistics", "size": "50-200", "website": ""},
            {"name": "Bharath Roadlines",        "industry": "Logistics", "size": "50-200", "website": ""},
            {"name": "QuickShip Express",        "industry": "Logistics", "size": "10-50",  "website": ""},
            {"name": "Steel Transport Co.",      "industry": "Logistics", "size": "10-50",  "website": ""},
        ],
        "contacts": [
            ("Speed Cargo Movers", {"first_name": "Mr.", "last_name": "Vinod Patel",   "title": "Plant manager (auto parts shipper)", "email": "vinod.p@example.com",  "phone": "+91 93330 11001"}),
            ("Bharath Roadlines",  {"first_name": "Mr.", "last_name": "Sunil Iyer",    "title": "Purchase head (textile mill)",       "email": "sunil.i@example.com",  "phone": "+91 93330 22001"}),
            ("QuickShip Express",  {"first_name": "Mr.", "last_name": "Anil Bose",     "title": "Owner (e-comm seller)",              "email": "anil.b@example.com",   "phone": "+91 93330 33001"}),
            ("Steel Transport Co.",{"first_name": "Mr.", "last_name": "Prakash Babu",  "title": "Logistics manager (steel plant)",    "email": "prakash.b@example.com","phone": "+91 93330 44001"}),
            ("Speed Cargo Movers", {"first_name": "Mr.", "last_name": "Karan Shah",    "title": "Buyer (new account)",                "email": "karan.s@example.com",  "phone": "+91 93330 11002"}),
        ],
        "deals": [
            ("Speed Cargo Movers", "Annual contract — Hosur to Pune (auto parts)",  "proposal",    875000, 60),
            ("Bharath Roadlines",  "Cotton bales — Coimbatore to Mumbai (6 mo)",    "negotiation", 540000, 75),
            ("QuickShip Express",  "Daily local pickup — e-comm (12 mo)",            "qualified",   320000, 40),
            ("Steel Transport Co.","TMT bars dispatch — Bellary to Bangalore",       "lead",        185000, 25),
            ("Speed Cargo Movers", "Q1 dispatch contract (closed)",                  "won",         420000, 100),
        ],
        "tasks": [
            {"title": "Send revised freight quote — Vinod (Hosur-Pune annual)",     "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Driver allocation for tomorrow's TMT bar dispatch",          "priority": "high",   "status": "open",        "due_offset": 1},
            {"title": "Follow up on overdue payment — Bharath Roadlines (₹3L)",     "priority": "normal", "status": "open",        "due_offset": -5},
            {"title": "Renew vehicle fitness for KA-01-MZ-1234",                    "priority": "normal", "status": "in_progress", "due_offset": 6},
            {"title": "Update GST e-way bills for last week's dispatches",          "priority": "low",    "status": "open",        "due_offset": 3},
        ],
        "invoices": [
            {"customer": "Speed Cargo Movers",  "issue_offset": -15, "due_offset": +15, "status": "sent",  "line_items": [{"description": "Hosur-Pune Q1 freight — 15 trips", "quantity": 15, "unit_price": 18500}], "tax_pct": 12},
            {"customer": "Bharath Roadlines",   "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Cotton bales freight — 8 trips", "quantity": 8, "unit_price": 22500}], "tax_pct": 12},
            {"customer": "QuickShip Express",   "issue_offset": -75, "due_offset": -45, "status": "paid",  "line_items": [{"description": "Daily pickup — month 3 (200 deliveries)", "quantity": 200, "unit_price": 180}], "tax_pct": 12},
            {"customer": "Steel Transport Co.", "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "TMT bars Bellary-Bangalore (5 trips est.)", "quantity": 5, "unit_price": 24000}], "tax_pct": 12},
        ],
    },

    # ── Construction / contracting ────────────────────────────────────────
    "Construction / contracting": {
        "icp": "Civil contractors, interior designers, home renovators (5-50 staff). Project-based ₹5L-₹2Cr.",
        "companies": [
            {"name": "BuildRight Contractors",      "industry": "Construction", "size": "10-50", "website": ""},
            {"name": "Saffron Interiors",           "industry": "Construction", "size": "10-50", "website": ""},
            {"name": "GreenSpace Renovations",      "industry": "Construction", "size": "1-10",  "website": ""},
            {"name": "Concrete Co. Civil",          "industry": "Construction", "size": "50-200","website": ""},
        ],
        "contacts": [
            ("BuildRight Contractors",  {"first_name": "Mr.", "last_name": "Rajiv Krishnan", "title": "Homeowner — 3BHK reno",  "email": "rajiv.k@example.com", "phone": "+91 92840 11001"}),
            ("Saffron Interiors",       {"first_name": "Mrs.","last_name": "Neha Verma",     "title": "Home owner — full interior", "email": "neha.v@example.com",   "phone": "+91 92840 22001"}),
            ("GreenSpace Renovations",  {"first_name": "Mr.", "last_name": "Sanjay Iyer",    "title": "Office renovation — 1500 sqft", "email": "sanjay.i@example.com","phone": "+91 92840 33001"}),
            ("Concrete Co. Civil",      {"first_name": "Mr.", "last_name": "Bharat Patel",   "title": "Builder — 4-floor apt project", "email": "bharat.p@example.com","phone": "+91 92840 44001"}),
            ("BuildRight Contractors",  {"first_name": "Mrs.","last_name": "Priya Reddy",    "title": "Kitchen + 2 bathroom upgrade",  "email": "priya.r@example.com", "phone": "+91 92840 11002"}),
        ],
        "deals": [
            ("Concrete Co. Civil",     "4-floor apartment civil work — Bharat",      "proposal",    8500000, 60),
            ("Saffron Interiors",      "Full home interiors — Neha (3BHK)",          "negotiation", 1450000, 75),
            ("BuildRight Contractors", "3BHK renovation — Rajiv Krishnan",            "qualified",    650000, 40),
            ("GreenSpace Renovations", "Office renovation 1500 sqft — Sanjay",        "lead",         425000, 25),
            ("BuildRight Contractors", "Kitchen + bath upgrade — Priya (closed)",     "won",          385000, 100),
        ],
        "tasks": [
            {"title": "Site visit + measurement — Neha's apartment (Sat 10 AM)",   "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send detailed BOQ + timeline to Bharat (Concrete Co.)",      "priority": "high",   "status": "open",        "due_offset": 1},
            {"title": "Follow up on milestone-2 payment — Rajiv (overdue 4 days)",  "priority": "normal", "status": "open",        "due_offset": -4},
            {"title": "Coordinate plumber + electrician for Priya's kitchen Mon",   "priority": "normal", "status": "in_progress", "due_offset": 3},
            {"title": "Procure tiles for GreenSpace office (need 2000 sq ft)",      "priority": "low",    "status": "open",        "due_offset": 7},
        ],
        "invoices": [
            {"customer": "BuildRight Contractors", "issue_offset": -12, "due_offset": +18, "status": "sent",  "line_items": [{"description": "3BHK renovation — milestone 2 (40%)", "quantity": 1, "unit_price": 260000}], "tax_pct": 18},
            {"customer": "Saffron Interiors",      "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Interior project advance (35%)", "quantity": 1, "unit_price": 507500}], "tax_pct": 18},
            {"customer": "Concrete Co. Civil",     "issue_offset": -75, "due_offset": -45, "status": "paid",  "line_items": [{"description": "Civil work — milestone 1 (20% advance)", "quantity": 1, "unit_price": 1700000}], "tax_pct": 18},
            {"customer": "GreenSpace Renovations", "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Office renovation estimate — 1500 sq ft", "quantity": 1, "unit_price": 425000}], "tax_pct": 18},
        ],
    },

    # ── Auto repair / garage ──────────────────────────────────────────────
    "Auto repair / garage": {
        "icp": "Independent garages, multi-brand service centres (2-15 staff). 30-200 cars/month. Local + repeat customers.",
        "companies": [
            {"name": "Speedo Auto Service",       "industry": "Automotive", "size": "1-10",  "website": ""},
            {"name": "PitStop Multi-brand Garage","industry": "Automotive", "size": "10-50", "website": ""},
            {"name": "BikeHub 2-wheeler Service", "industry": "Automotive", "size": "1-10",  "website": ""},
            {"name": "Premium Car Detailing Co.", "industry": "Automotive", "size": "1-10",  "website": ""},
        ],
        "contacts": [
            ("Speedo Auto Service",        {"first_name": "Mr.", "last_name": "Vivek Sharma",  "title": "Honda City owner (KA-01)",      "email": "vivek.s@example.com",  "phone": "+91 91610 11001"}),
            ("PitStop Multi-brand Garage", {"first_name": "Mrs.","last_name": "Anita Krishnan","title": "Hyundai i20 (KA-05)",            "email": "anita.k@example.com",  "phone": "+91 91610 22001"}),
            ("BikeHub 2-wheeler Service",  {"first_name": "Mr.", "last_name": "Karthik Reddy", "title": "Royal Enfield owner",            "email": "karthik.r@example.com","phone": "+91 91610 33001"}),
            ("Premium Car Detailing Co.",  {"first_name": "Mr.", "last_name": "Aditya Pillai", "title": "BMW 3-series detailing client",  "email": "aditya.p@example.com", "phone": "+91 91610 44001"}),
            ("Speedo Auto Service",        {"first_name": "Mr.", "last_name": "Sunil Babu",    "title": "Maruti Swift — regular",         "email": "sunil.b@example.com",  "phone": "+91 91610 11002"}),
        ],
        "deals": [
            ("PitStop Multi-brand Garage", "Engine overhaul — Anita's i20",            "proposal",    32000, 70),
            ("Premium Car Detailing Co.",  "Annual detailing package — Aditya BMW",    "negotiation", 18000, 80),
            ("Speedo Auto Service",        "Major service + tyres — Vivek Honda City", "qualified",   8500,  40),
            ("BikeHub 2-wheeler Service",  "Royal Enfield restoration — Karthik",      "lead",        12000, 25),
            ("Speedo Auto Service",        "Regular service — Sunil Swift (closed)",   "won",         3500,  100),
        ],
        "tasks": [
            {"title": "Call Vivek with engine diagnostic results (Honda City)",  "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send detailing schedule to Aditya (3 sessions over Nov)",  "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Order spare parts for Anita's engine overhaul (i20)",      "priority": "normal", "status": "in_progress", "due_offset": 1},
            {"title": "Follow up — Karthik's Royal Enfield restoration approval", "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Maintenance reminder broadcast to monthly regulars",       "priority": "low",    "status": "open",        "due_offset": 5},
        ],
        "invoices": [
            {"customer": "PitStop Multi-brand Garage", "issue_offset": -5,  "due_offset": +5,  "status": "sent",  "line_items": [{"description": "Engine diagnostic + advance (i20)", "quantity": 1, "unit_price": 6500}], "tax_pct": 18},
            {"customer": "Premium Car Detailing Co.",  "issue_offset": -30, "due_offset": -5,  "status": "sent",  "line_items": [{"description": "Premium detailing session 1 (BMW)", "quantity": 1, "unit_price": 6500}], "tax_pct": 18},
            {"customer": "Speedo Auto Service",        "issue_offset": -55, "due_offset": -25, "status": "paid",  "line_items": [{"description": "Major service — Swift (Sunil B.)", "quantity": 1, "unit_price": 3500}], "tax_pct": 18},
            {"customer": "BikeHub 2-wheeler Service",  "issue_offset":  0,  "due_offset":  7,  "status": "draft", "line_items": [{"description": "Royal Enfield restoration estimate", "quantity": 1, "unit_price": 12000}], "tax_pct": 18},
        ],
    },

    # ── Photography / event services ──────────────────────────────────────
    "Photography / event services": {
        "icp": "Wedding photographers, event planners, freelance videographers (1-10 staff). 30-200 events/year.",
        "companies": [
            {"name": "FrameStory Photography",   "industry": "Photography", "size": "1-10", "website": ""},
            {"name": "Eternal Moments Studio",   "industry": "Photography", "size": "1-10", "website": ""},
            {"name": "Lens Republic Films",      "industry": "Photography", "size": "1-10", "website": ""},
            {"name": "Confetti Event Planners",  "industry": "Photography", "size": "10-50","website": ""},
        ],
        "contacts": [
            ("FrameStory Photography",  {"first_name": "Mr.",  "last_name": "Rohit Iyer",      "title": "Wedding — Dec 2025",          "email": "rohit.i@example.com",  "phone": "+91 91290 11001"}),
            ("Eternal Moments Studio",  {"first_name": "Mrs.", "last_name": "Anjali Sharma",   "title": "Pre-wedding + wedding",       "email": "anjali.s@example.com", "phone": "+91 91290 22001"}),
            ("Lens Republic Films",     {"first_name": "Mr.",  "last_name": "Karan Pillai",    "title": "Corporate film inquiry",      "email": "karan.p@example.com",  "phone": "+91 91290 33001"}),
            ("Confetti Event Planners", {"first_name": "Mrs.", "last_name": "Pooja Kapoor",    "title": "Daughter's first birthday",   "email": "pooja.k@example.com",  "phone": "+91 91290 44001"}),
            ("FrameStory Photography",  {"first_name": "Mr.",  "last_name": "Aditya Reddy",    "title": "Maternity shoot inquiry",     "email": "aditya.r@example.com", "phone": "+91 91290 11002"}),
        ],
        "deals": [
            ("Eternal Moments Studio",  "Wedding + pre-wedding bundle — Anjali",        "negotiation", 285000, 75),
            ("FrameStory Photography",  "Wedding 3-day bundle — Rohit Iyer",            "proposal",    175000, 60),
            ("Confetti Event Planners", "First-birthday — Pooja's daughter (Sat)",      "qualified",    85000, 50),
            ("Lens Republic Films",     "Corporate brand film — Karan (3 min)",         "lead",        125000, 25),
            ("FrameStory Photography",  "Maternity shoot — Aditya's wife (closed)",     "won",          22000, 100),
        ],
        "tasks": [
            {"title": "Send Anjali's wedding contract + advance link (₹85k)",        "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Prep equipment + run-through for Pooja's birthday Sat",        "priority": "high",   "status": "open",        "due_offset": 2},
            {"title": "Follow up — Karan's corporate film brief (5 days idle)",       "priority": "normal", "status": "open",        "due_offset": -3},
            {"title": "Deliver Rohit's pre-wedding photos (gallery + 3 prints)",       "priority": "normal", "status": "in_progress", "due_offset": 4},
            {"title": "Update Instagram with last weekend's wedding highlights",      "priority": "low",    "status": "open",        "due_offset": 1},
        ],
        "invoices": [
            {"customer": "Eternal Moments Studio",  "issue_offset": -8,  "due_offset": +22, "status": "sent",  "line_items": [{"description": "Wedding bundle advance (30%)", "quantity": 1, "unit_price": 85500}], "tax_pct": 18},
            {"customer": "FrameStory Photography",  "issue_offset": -30, "due_offset": -5,  "status": "sent",  "line_items": [{"description": "Pre-wedding shoot — Rohit Iyer", "quantity": 1, "unit_price": 45000}], "tax_pct": 18},
            {"customer": "Confetti Event Planners", "issue_offset": -60, "due_offset": -30, "status": "paid",  "line_items": [{"description": "Family portrait session (paid)", "quantity": 1, "unit_price": 18000}], "tax_pct": 18},
            {"customer": "Lens Republic Films",     "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Corporate brand film estimate (3 min)", "quantity": 1, "unit_price": 125000}], "tax_pct": 18},
        ],
    },

    # ── Travel / tour operator ────────────────────────────────────────────
    "Travel / tour operator": {
        "icp": "Tour operators, travel agencies, destination management cos (3-30 staff). Domestic + outbound, group + custom.",
        "companies": [
            {"name": "Wanderlust Holidays",         "industry": "Travel", "size": "10-50", "website": ""},
            {"name": "Himalayan Trail Adventures",  "industry": "Travel", "size": "1-10",  "website": ""},
            {"name": "DreamScape Honeymoons",       "industry": "Travel", "size": "1-10",  "website": ""},
            {"name": "Bharat Heritage Tours",       "industry": "Travel", "size": "10-50", "website": ""},
        ],
        "contacts": [
            ("Wanderlust Holidays",        {"first_name": "Mrs.","last_name": "Sneha Iyer",     "title": "Family trip — Bali (4 pax)",       "email": "sneha.i@example.com",  "phone": "+91 90840 11001"}),
            ("Himalayan Trail Adventures", {"first_name": "Mr.", "last_name": "Aditya Verma",   "title": "Trek to EBC — solo",                "email": "aditya.v@example.com", "phone": "+91 90840 22001"}),
            ("DreamScape Honeymoons",      {"first_name": "Mr.", "last_name": "Karan Mehta",    "title": "Honeymoon — Maldives 6N",           "email": "karan.m@example.com",  "phone": "+91 90840 33001"}),
            ("Bharat Heritage Tours",      {"first_name": "Mrs.","last_name": "Priya Bhat",     "title": "Senior parents — Rajasthan 8 days", "email": "priya.b@example.com",  "phone": "+91 90840 44001"}),
            ("Wanderlust Holidays",        {"first_name": "Mr.", "last_name": "Vikram Joshi",   "title": "Corporate offsite — 50 pax",        "email": "vikram.j@example.com", "phone": "+91 90840 11002"}),
        ],
        "deals": [
            ("DreamScape Honeymoons",      "Maldives 6N honeymoon — Karan + spouse",         "negotiation", 285000, 80),
            ("Bharat Heritage Tours",      "Rajasthan 8-day — Priya's parents",              "proposal",    145000, 60),
            ("Wanderlust Holidays",        "Bali family trip — Sneha (4 pax)",               "qualified",   220000, 50),
            ("Himalayan Trail Adventures", "EBC trek — Aditya (solo)",                       "lead",         95000, 25),
            ("Wanderlust Holidays",        "Corporate offsite — 50 pax Goa (closed)",        "won",         450000, 100),
        ],
        "tasks": [
            {"title": "Send Karan honeymoon v2 itinerary (Maldives + Bora extension)", "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Confirm hotel block for Priya's parents Rajasthan trip",          "priority": "high",   "status": "open",        "due_offset": 1},
            {"title": "Follow up on Aditya EBC permit + insurance documents",            "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Pre-departure check-in with Sneha (Bali family trip, dep Mon)",   "priority": "normal", "status": "in_progress", "due_offset": 4},
            {"title": "Update website with new domestic destinations for Q4",            "priority": "low",    "status": "open",        "due_offset": 7},
        ],
        "invoices": [
            {"customer": "DreamScape Honeymoons",      "issue_offset": -10, "due_offset": +20, "status": "sent",  "line_items": [{"description": "Maldives honeymoon advance (50%)", "quantity": 1, "unit_price": 142500}], "tax_pct": 5},
            {"customer": "Bharat Heritage Tours",      "issue_offset": -35, "due_offset": -5,  "status": "sent",  "line_items": [{"description": "Rajasthan 8-day — full payment", "quantity": 1, "unit_price": 145000}], "tax_pct": 5},
            {"customer": "Wanderlust Holidays",        "issue_offset": -65, "due_offset": -35, "status": "paid",  "line_items": [{"description": "Corporate Goa offsite — 50 pax (paid)", "quantity": 1, "unit_price": 450000}], "tax_pct": 5},
            {"customer": "Himalayan Trail Adventures", "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "EBC trek estimate — solo (Aditya V.)", "quantity": 1, "unit_price": 95000}], "tax_pct": 5},
        ],
    },

    # ── Real estate broker ────────────────────────────────────────────────
    "Real estate broker": {
        "icp": "Independent property brokers + small agencies (1-10 staff). Rental + resale mix. Hyperlocal expertise.",
        "companies": [
            {"name": "Prestige Lakeside Habitat",  "industry": "Real estate", "size": "200-1000", "website": ""},
            {"name": "Sobha Indraprastha Towers",  "industry": "Real estate", "size": "200-1000", "website": ""},
            {"name": "Brigade Cosmopolis",         "industry": "Real estate", "size": "200-1000", "website": ""},
            {"name": "Independent villa (Whitefield)","industry": "Real estate","size": "1-10",   "website": ""},
        ],
        "contacts": [
            ("Prestige Lakeside Habitat",      {"first_name": "Mr.",  "last_name": "Anand Sharma",   "title": "Buyer — 3BHK ₹1.6Cr budget",     "email": "anand.s@example.com",  "phone": "+91 90160 11001"}),
            ("Sobha Indraprastha Towers",      {"first_name": "Mrs.", "last_name": "Sneha Iyer",     "title": "Buyer — 2BHK rental seeker",      "email": "sneha.i@example.com",  "phone": "+91 90160 22001"}),
            ("Brigade Cosmopolis",             {"first_name": "Mr.",  "last_name": "Rajesh Pillai",  "title": "NRI — investment property",       "email": "rajesh.p@example.com", "phone": "+91 90160 33001"}),
            ("Independent villa (Whitefield)", {"first_name": "Mr.",  "last_name": "Vinod Kapoor",   "title": "Seller — owner (4BHK villa)",     "email": "vinod.k@example.com",  "phone": "+91 90160 44001"}),
            ("Prestige Lakeside Habitat",      {"first_name": "Ms.",  "last_name": "Divya Krishnan", "title": "Tenant — found via property site","email": "divya.k@example.com",  "phone": "+91 90160 11002"}),
        ],
        "deals": [
            ("Prestige Lakeside Habitat", "3BHK purchase ₹1.6Cr — Anand Sharma",       "negotiation", 16000000, 70),
            ("Sobha Indraprastha Towers", "2BHK rental — Sneha Iyer",                  "proposal",      48000, 75),
            ("Brigade Cosmopolis",        "Investment 2BHK — Rajesh (NRI)",            "qualified",  12500000, 40),
            ("Independent villa (Whitefield)","4BHK villa sale — Vinod (owner)",       "lead",       28000000, 20),
            ("Prestige Lakeside Habitat", "2BHK rental — Divya (closed)",              "won",           45000, 100),
        ],
        "tasks": [
            {"title": "Schedule Anand's 3BHK final site visit + token decision",      "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Send 3 rental shortlist options to Sneha (₹45-50k budget)",     "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Follow up — Rajesh hasn't responded to investment shortlist",   "priority": "normal", "status": "open",        "due_offset": -3},
            {"title": "Get verified property documents from Vinod (villa seller)",     "priority": "normal", "status": "in_progress", "due_offset": 2},
            {"title": "Renew RERA registration for portfolio (annual)",                "priority": "low",    "status": "open",        "due_offset": 30},
        ],
        "invoices": [
            {"customer": "Prestige Lakeside Habitat", "issue_offset": -5,  "due_offset": +25, "status": "sent",  "line_items": [{"description": "Rental brokerage — Divya K. (1 month)", "quantity": 1, "unit_price": 45000}], "tax_pct": 18},
            {"customer": "Sobha Indraprastha Towers", "issue_offset": -40, "due_offset": -10, "status": "sent",  "line_items": [{"description": "Rental brokerage advance — Sneha I.", "quantity": 1, "unit_price": 24000}], "tax_pct": 18},
            {"customer": "Brigade Cosmopolis",        "issue_offset": -75, "due_offset": -45, "status": "paid",  "line_items": [{"description": "2BHK resale brokerage (Q4 closing)", "quantity": 1, "unit_price": 125000}], "tax_pct": 18},
            {"customer": "Independent villa (Whitefield)", "issue_offset": 0, "due_offset": 30, "status": "draft", "line_items": [{"description": "Villa sale brokerage estimate (1% of ₹2.8Cr)", "quantity": 1, "unit_price": 280000}], "tax_pct": 18},
        ],
    },

    # ── Consulting ────────────────────────────────────────────────────────
    "Consulting": {
        "icp": (
            "Independent consultants and small consulting boutiques (1-15 staff) "
            "in strategy, ops, HR, marketing, or tech. Decision-maker is the "
            "founder. Sweet spot: ₹50L-₹3Cr annual revenue, project-based."
        ),
        "companies": [
            {"name": "Nexus Strategy Group",    "industry": "Consulting", "size": "10-50",   "website": "nexusstrategy.example.in"},
            {"name": "Pivot Marketing",         "industry": "Consulting", "size": "1-10",    "website": "pivot.example.in"},
            {"name": "ScaleUp HR Consulting",   "industry": "Consulting", "size": "10-50",   "website": "scaleuphr.example.in"},
            {"name": "Orbit Tech Advisory",     "industry": "Consulting", "size": "1-10",    "website": "orbit.example.in"},
        ],
        "contacts": [
            ("Nexus Strategy Group",   {"first_name": "Mr.",  "last_name": "Rohit Bhatia",      "title": "Client — GTM strategy",      "email": "rohit.b@example.com",   "phone": "+91 95400 11001"}),
            ("Pivot Marketing",        {"first_name": "Ms.",  "last_name": "Sneha Pillai",      "title": "Client — brand revamp",       "email": "sneha.p@example.com",   "phone": "+91 95400 22001"}),
            ("ScaleUp HR Consulting",  {"first_name": "Mr.",  "last_name": "Anil Krishnan",     "title": "Client — leadership hiring",  "email": "anil.k@example.com",    "phone": "+91 95400 33001"}),
            ("Orbit Tech Advisory",    {"first_name": "Mrs.", "last_name": "Divya Menon",       "title": "Client — cloud migration",    "email": "divya.m@example.com",   "phone": "+91 95400 44001"}),
            ("Nexus Strategy Group",   {"first_name": "Mr.",  "last_name": "Vikram Iyer",       "title": "Repeat client — Q2 retainer", "email": "vikram.i@example.com",  "phone": "+91 95400 11002"}),
        ],
        "deals": [
            ("Nexus Strategy Group",   "GTM strategy engagement — Rohit (12 weeks)",     "proposal",    450000, 60),
            ("Pivot Marketing",        "Brand revamp project — Sneha (8 weeks)",          "negotiation", 285000, 80),
            ("ScaleUp HR Consulting",  "Leadership hiring — 3 senior roles",              "qualified",   180000, 40),
            ("Orbit Tech Advisory",    "Cloud migration assessment — Divya (4 weeks)",    "lead",        125000, 25),
            ("Nexus Strategy Group",   "Q2 retainer — Vikram Iyer (closed)",              "won",         360000, 100),
        ],
        "tasks": [
            {"title": "Send GTM project proposal v2 — Rohit Bhatia",               "priority": "high",   "status": "open",        "due_offset": 0},
            {"title": "Kickoff call — Sneha brand-revamp project (Wed)",            "priority": "high",   "status": "open",        "due_offset": 2},
            {"title": "Follow up — Anil hiring brief (5 days idle)",                "priority": "normal", "status": "open",        "due_offset": -2},
            {"title": "Compile cloud assessment scope doc — Divya",                 "priority": "normal", "status": "in_progress", "due_offset": 4},
            {"title": "Schedule Q3 retainer review — Vikram",                       "priority": "normal", "status": "open",        "due_offset": 6},
            {"title": "Update consultancy website case studies (Q1 wins)",          "priority": "low",    "status": "open",        "due_offset": 10},
        ],
        "invoices": [
            {"customer": "Nexus Strategy Group",   "issue_offset": -14, "due_offset": +16, "status": "sent",  "line_items": [{"description": "GTM project — milestone 1 (week 4)", "quantity": 1, "unit_price": 150000}], "tax_pct": 18},
            {"customer": "Pivot Marketing",        "issue_offset": -45, "due_offset": -15, "status": "sent",  "line_items": [{"description": "Brand revamp — phase 1 advance", "quantity": 1, "unit_price": 95000}], "tax_pct": 18},
            {"customer": "ScaleUp HR Consulting",  "issue_offset": -75, "due_offset": -45, "status": "paid",  "line_items": [{"description": "Leadership hiring — search fee (1 role)", "quantity": 1, "unit_price": 60000}], "tax_pct": 18},
            {"customer": "Orbit Tech Advisory",    "issue_offset":  0,  "due_offset":  30, "status": "draft", "line_items": [{"description": "Cloud migration assessment — proposal", "quantity": 1, "unit_price": 125000}], "tax_pct": 18},
        ],
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────

def _has_existing_data(business_id: str) -> bool:
    """Refuse to seed if the business already has CRM data — same safety
    guard as the generic seed_data.py so the two seeders never collide."""
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


def _resolve_industry(industry: Optional[str]) -> Optional[str]:
    """Case-insensitive match against keys in INDUSTRY_DATA. Returns None
    if no match — caller should fall through to generic seed_data.py."""
    if not industry:
        return None
    needle = industry.strip().lower()
    for key in INDUSTRY_DATA:
        if key.lower() == needle:
            return key
    return None


def _create_companies(business_id: str, user_id: str, specs: List[Dict]) -> Dict[str, str]:
    """Returns {name → id} so the next stages can resolve customer references."""
    out: Dict[str, str] = {}
    for spec in specs:
        try:
            row = _crm.create_company(business_id, user_id, {
                "name":     spec["name"],
                "industry": spec.get("industry") or "",
                "size":     spec.get("size") or "",
                "website":  spec.get("website") or "",
            })
            out[spec["name"]] = row["id"]
        except Exception as e:
            logger.warning(f"[IndustrySeed] company '{spec['name']}' failed: {e}")
    return out


def _create_contacts(business_id: str, user_id: str, specs: List, company_ids: Dict[str, str]) -> Dict[str, str]:
    """Returns {email → contact_id}. Source set to 'manual' so the Leads-tab
    source filter has something to show even on the industry seed path."""
    out: Dict[str, str] = {}
    for company_name, person in specs:
        try:
            row = _crm.create_contact(business_id, user_id, {
                "first_name": person.get("first_name") or "",
                "last_name":  person.get("last_name") or "",
                "title":      person.get("title") or "",
                "email":      person.get("email") or "",
                "phone":      person.get("phone") or "",
                "company_id": company_ids.get(company_name),
                "source":     "manual",
            })
            email = (person.get("email") or "").strip().lower()
            if email:
                out[email] = row["id"]
        except Exception as e:
            logger.warning(f"[IndustrySeed] contact '{person.get('first_name')}' failed: {e}")
    return out


def _create_deals(business_id: str, user_id: str, specs: List, company_ids: Dict[str, str]) -> int:
    n = 0
    for company_name, deal_name, stage, value, prob in specs:
        try:
            _crm.create_deal(business_id, user_id, {
                "name":             deal_name,
                "stage":            stage,
                "value":            value,
                "currency":         "INR",
                "probability_pct":  prob,
                "company_id":       company_ids.get(company_name),
            })
            n += 1
        except Exception as e:
            logger.warning(f"[IndustrySeed] deal '{deal_name}' failed: {e}")
    return n


def _create_tasks(business_id: str, user_id: str, specs: List[Dict]) -> int:
    today = date.today()
    n = 0
    for spec in specs:
        try:
            due = today + timedelta(days=int(spec.get("due_offset", 0)))
            _tasks.create_task(business_id, user_id, {
                "title":    spec["title"],
                "priority": spec.get("priority", "normal"),
                "status":   spec.get("status", "open"),
                "due_date": due.isoformat(),
            })
            n += 1
        except Exception as e:
            logger.warning(f"[IndustrySeed] task '{spec.get('title')}' failed: {e}")
    return n


def _create_invoices(business_id: str, user_id: str, specs: List[Dict], company_ids: Dict[str, str]) -> int:
    today = date.today()
    n = 0
    for spec in specs:
        try:
            issue = (today + timedelta(days=int(spec.get("issue_offset", 0)))).isoformat()
            due = (today + timedelta(days=int(spec.get("due_offset", 30)))).isoformat()
            _inv.create_invoice(business_id, user_id, {
                "customer_name":       spec["customer"],
                "customer_company_id": company_ids.get(spec["customer"]),
                "line_items":          spec["line_items"],
                "tax_pct":             spec.get("tax_pct", 18),
                "currency":            "INR",
                "issue_date":          issue,
                "due_date":            due,
                "status":              spec.get("status", "draft"),
            })
            n += 1
        except Exception as e:
            logger.warning(f"[IndustrySeed] invoice for '{spec.get('customer')}' failed: {e}")
    return n


# ── Public entry point ───────────────────────────────────────────────────

def seed_industry_sample(business_id: str, user_id: str, industry: Optional[str]) -> Dict[str, Any]:
    """Drop industry-tailored sample data into an empty workspace.

    Returns a result dict with counts and the matched industry key, or a
    `{seeded: False, reason: ...}` shape if we refused (existing data or
    industry not recognised).

    Caller responsibility: this is idempotent on data-existence but NOT on
    being called twice in parallel — the existence check is non-locking.
    Acceptable for an onboarding flow that runs once per business.
    """
    matched = _resolve_industry(industry)
    if not matched:
        return {"seeded": False, "reason": "industry_unknown", "industry": industry}

    if _has_existing_data(business_id):
        return {"seeded": False, "reason": "existing_data", "industry": matched}

    data = INDUSTRY_DATA[matched]
    company_ids = _create_companies(business_id, user_id, data.get("companies", []))
    contact_count = len(_create_contacts(business_id, user_id, data.get("contacts", []), company_ids))
    deal_count = _create_deals(business_id, user_id, data.get("deals", []), company_ids)
    task_count = _create_tasks(business_id, user_id, data.get("tasks", []))
    invoice_count = _create_invoices(business_id, user_id, data.get("invoices", []), company_ids)

    logger.info(
        f"[IndustrySeed] biz={business_id} industry={matched} → "
        f"companies={len(company_ids)} contacts={contact_count} "
        f"deals={deal_count} tasks={task_count} invoices={invoice_count}"
    )

    return {
        "seeded": True,
        "industry": matched,
        "icp": data.get("icp", ""),
        "counts": {
            "companies": len(company_ids),
            "contacts":  contact_count,
            "deals":     deal_count,
            "tasks":     task_count,
            "invoices":  invoice_count,
        },
    }
