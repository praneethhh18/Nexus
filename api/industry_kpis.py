"""Industry-aware KPI computation.

Phase A/B renamed the KPI LABELS per industry ("Upcoming appointments" for
Healthcare, "Active listings" for Real estate, etc.). This module computes
the matching VALUES — because "Upcoming appointments" showing pipeline ₹
value is misleading; it should be a count of appointments.

Design:
    Each industry has a compute function that takes the standard CRM data
    bundle (deals, tasks, invoices, crm_overview) and returns 4 KPI tiles:
        [{label, value, sub, tone}, ...]

    Tiles are returned in display order. The frontend renders them in the
    dashboard KPI strip, using the label/value/sub directly — no further
    transformation. `tone` is one of "warn", "ok", "info", "err" (mapped
    to dashboard colour CSS variables).

    For industries we haven't tuned, `compute_kpis` falls through to a
    generic CRM tile set so the dashboard still renders correctly.

Computation runs in-process from already-fetched data — no extra DB
round-trips. The dashboard endpoint passes the data bundle in; the
result is cached on the frontend via the existing dataCache layer.
"""
from __future__ import annotations

from datetime import date
from typing import Any, Callable, Dict, List, Optional


# ── Helpers ──────────────────────────────────────────────────────────────

def _money_inr(v: Optional[float]) -> str:
    try:
        n = float(v or 0)
    except Exception:
        n = 0.0
    # Indian-format with no decimals for display — frontend re-formats if needed
    if n >= 100000:
        return f"₹{n/100000:.1f}L"
    return f"₹{int(round(n)):,}"


def _deals_by_stage(pipe: dict) -> dict:
    """Pull deals-by-stage counts from the pipeline payload safely."""
    return ((pipe or {}).get("by_stage") or {})


def _open_count(pipe: dict) -> int:
    bs = _deals_by_stage(pipe)
    return sum(
        int((bs.get(stage) or {}).get("count", 0))
        for stage in ("lead", "qualified", "proposal", "negotiation")
    )


def _open_value(pipe: dict) -> float:
    bs = _deals_by_stage(pipe)
    return float(sum(
        float((bs.get(stage) or {}).get("total") or 0)
        for stage in ("lead", "qualified", "proposal", "negotiation")
    ))


def _confirmed_count(pipe: dict) -> int:
    """Higher-confidence deals — proposal + negotiation. For Healthcare these
    map to scheduled-but-not-completed appointments; for Real estate the
    near-closing transactions; etc."""
    bs = _deals_by_stage(pipe)
    return sum(int((bs.get(stage) or {}).get("count", 0)) for stage in ("proposal", "negotiation"))


def _won_this_month_count(pipe: dict) -> int:
    return int((_deals_by_stage(pipe).get("won") or {}).get("count", 0))


def _won_this_month_value(crm: dict) -> float:
    return float((crm or {}).get("won_this_month") or 0)


def _outstanding_count(inv: dict) -> int:
    return int(((inv or {}).get("outstanding") or {}).get("count", 0))


def _outstanding_value(inv: dict) -> float:
    return float(((inv or {}).get("outstanding") or {}).get("total") or 0)


def _overdue_invoices(inv: dict) -> int:
    return int(((inv or {}).get("overdue") or {}).get("count", 0))


def _overdue_tasks(tasks: dict) -> int:
    return int((tasks or {}).get("overdue") or 0)


# ── Per-industry tile builders ───────────────────────────────────────────
# Each takes the shared bundle and returns a 4-tile list. The label is
# already the industry-appropriate noun (matches what frontend renders
# from useTerm()'s kpi_* keys), so the values agree with the labels.

KpiTile = Dict[str, Any]
BundleFn = Callable[[dict, dict, dict, dict], List[KpiTile]]


def _healthcare(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Upcoming appointments", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} total in pipeline", "tone": "warn"},
        {"label": "Treatments this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " billed", "tone": "ok"},
        {"label": "Pending bills", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " outstanding", "tone": "info"},
        {"label": "Overdue follow-ups", "value": _overdue_tasks(tasks) + _overdue_invoices(invoices),
         "sub": f"{_overdue_tasks(tasks)} tasks · {_overdue_invoices(invoices)} bills", "tone": "err"},
    ]


def _real_estate_broker(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Active closures", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)) + " in pipeline", "tone": "warn"},
        {"label": "Closures this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " value", "tone": "ok"},
        {"label": "Brokerage pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " due", "tone": "info"},
        {"label": "Stalled inquiries", "value": _overdue_tasks(tasks),
         "sub": "follow-ups overdue", "tone": "err"},
    ]


def _real_estate(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Active listings", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)) + " pipeline", "tone": "warn"},
        {"label": "Closed this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " value", "tone": "ok"},
        {"label": "Pending brokerage", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " outstanding", "tone": "info"},
        {"label": "Stalled deals", "value": _overdue_tasks(tasks),
         "sub": "deals untouched 7+ days", "tone": "err"},
    ]


def _education(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Open applications", "value": _open_count(pipe),
         "sub": f"{_confirmed_count(pipe)} close to confirming", "tone": "warn"},
        {"label": "Admissions this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " in fees", "tone": "ok"},
        {"label": "Fees pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " outstanding", "tone": "info"},
        {"label": "Overdue fees", "value": _overdue_invoices(invoices),
         "sub": f"{_overdue_tasks(tasks)} parent calls overdue", "tone": "err"},
    ]


def _tutoring(pipe, tasks, invoices, crm) -> List[KpiTile]:
    # Tutoring: active enrolments matter more than "value pipeline"
    return [
        {"label": "Active enrolments", "value": _open_count(pipe) + _won_this_month_count(pipe),
         "sub": f"{_open_count(pipe)} pending · {_won_this_month_count(pipe)} this month", "tone": "warn"},
        {"label": "New enrolments this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " in fees", "tone": "ok"},
        {"label": "Fees pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " due", "tone": "info"},
        {"label": "Overdue fees", "value": _overdue_invoices(invoices),
         "sub": "parents to follow up with", "tone": "err"},
    ]


def _legal(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Active matters", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)) + " engaged", "tone": "warn"},
        {"label": "Closed this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Fees pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Overdue tasks", "value": _overdue_tasks(tasks),
         "sub": f"{_overdue_invoices(invoices)} fee invoices past due", "tone": "err"},
    ]


def _ecommerce(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Open orders", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)) + " in flight", "tone": "warn"},
        {"label": "Orders shipped", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " month", "tone": "ok"},
        {"label": "Invoices pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " due", "tone": "info"},
        {"label": "Returns + complaints", "value": _overdue_tasks(tasks),
         "sub": "support tasks overdue", "tone": "err"},
    ]


def _finance(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Active engagements", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)), "tone": "warn"},
        {"label": "Closed this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Fees pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Compliance due", "value": _overdue_tasks(tasks),
         "sub": "filings/tasks overdue", "tone": "err"},
    ]


def _saas(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Pipeline (ARR)", "value": _money_inr(_open_value(pipe)),
         "sub": f"{_open_count(pipe)} accounts", "tone": "warn"},
        {"label": "Closed this month", "value": _money_inr(_won_this_month_value(crm)),
         "sub": f"{_won_this_month_count(pipe)} accounts", "tone": "ok"},
        {"label": "Subscriptions pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "At-risk renewals", "value": _overdue_tasks(tasks),
         "sub": "follow-ups overdue", "tone": "err"},
    ]


def _manufacturing(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Open POs", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)) + " value", "tone": "warn"},
        {"label": "Delivered this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Invoices pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " due", "tone": "info"},
        {"label": "Overdue dispatches", "value": _overdue_tasks(tasks),
         "sub": "actions overdue", "tone": "err"},
    ]


def _hospitality(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Upcoming bookings", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} inquiries open", "tone": "warn"},
        {"label": "Checked in this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Pending payments", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Unconfirmed bookings", "value": _overdue_tasks(tasks),
         "sub": "follow-ups due", "tone": "err"},
    ]


def _restaurant(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Upcoming reservations", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} inquiries", "tone": "warn"},
        {"label": "Catering orders this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Pending payments", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Reservation no-shows", "value": _overdue_tasks(tasks),
         "sub": "needs follow-up", "tone": "err"},
    ]


def _local_services(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Scheduled jobs", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} quotes pending", "tone": "warn"},
        {"label": "Jobs completed", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Pending payments", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " owed", "tone": "info"},
        {"label": "Overdue follow-ups", "value": _overdue_tasks(tasks),
         "sub": "customers waiting", "tone": "err"},
    ]


def _salon(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Upcoming appointments", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} pending confirmation", "tone": "warn"},
        {"label": "Services this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " revenue", "tone": "ok"},
        {"label": "Bills pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Rebook reminders due", "value": _overdue_tasks(tasks),
         "sub": "regulars to nudge", "tone": "err"},
    ]


def _garment_retail(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Open orders", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)), "tone": "warn"},
        {"label": "Orders shipped", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Invoices pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Overdue wholesale dues", "value": _overdue_invoices(invoices),
         "sub": f"{_overdue_tasks(tasks)} buyer follow-ups", "tone": "err"},
    ]


def _logistics(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Active dispatches", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} bookings open", "tone": "warn"},
        {"label": "Delivered this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Freight pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)) + " due", "tone": "info"},
        {"label": "Stuck shipments", "value": _overdue_tasks(tasks),
         "sub": "ops follow-ups due", "tone": "err"},
    ]


def _construction(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Active projects", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)) + " contracted", "tone": "warn"},
        {"label": "Milestones completed", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " month", "tone": "ok"},
        {"label": "Milestone payments due", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Site escalations", "value": _overdue_tasks(tasks),
         "sub": "tasks overdue", "tone": "err"},
    ]


def _auto_repair(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Vehicles in service", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} estimates pending", "tone": "warn"},
        {"label": "Jobs completed", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)) + " revenue", "tone": "ok"},
        {"label": "Bills pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Service reminders due", "value": _overdue_tasks(tasks),
         "sub": "customers to call", "tone": "err"},
    ]


def _photography(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Upcoming shoots", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} inquiries open", "tone": "warn"},
        {"label": "Events this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Payments pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Delivery overdue", "value": _overdue_tasks(tasks),
         "sub": "galleries to ship", "tone": "err"},
    ]


def _travel(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Upcoming trips", "value": _confirmed_count(pipe),
         "sub": f"{_open_count(pipe)} inquiries open", "tone": "warn"},
        {"label": "Trips completed", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Payments pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Document collection due", "value": _overdue_tasks(tasks),
         "sub": "travellers to follow up", "tone": "err"},
    ]


def _consulting(pipe, tasks, invoices, crm) -> List[KpiTile]:
    return [
        {"label": "Active engagements", "value": _open_count(pipe),
         "sub": _money_inr(_open_value(pipe)) + " engaged", "tone": "warn"},
        {"label": "Closed this month", "value": _won_this_month_count(pipe),
         "sub": _money_inr(_won_this_month_value(crm)), "tone": "ok"},
        {"label": "Invoices pending", "value": _outstanding_count(invoices),
         "sub": _money_inr(_outstanding_value(invoices)), "tone": "info"},
        {"label": "Project blockers", "value": _overdue_tasks(tasks),
         "sub": "tasks overdue", "tone": "err"},
    ]


def _generic(pipe, tasks, invoices, crm) -> List[KpiTile]:
    """Fallback for unknown industries — matches the current Dashboard.jsx
    KPI cards (Open pipeline / Won this month / Outstanding invoices /
    Overdue)."""
    return [
        {"label": "Open pipeline", "value": _money_inr(_open_value(pipe)),
         "sub": f"{_open_count(pipe)} deals", "tone": "warn"},
        {"label": "Won this month", "value": _money_inr(_won_this_month_value(crm)),
         "sub": f"{_won_this_month_count(pipe)} closed", "tone": "ok"},
        {"label": "Outstanding invoices", "value": _money_inr(_outstanding_value(invoices)),
         "sub": f"{_outstanding_count(invoices)} unpaid", "tone": "info"},
        {"label": "Overdue", "value": _overdue_tasks(tasks) + _overdue_invoices(invoices),
         "sub": f"{_overdue_tasks(tasks)} tasks · {_overdue_invoices(invoices)} invoices", "tone": "err"},
    ]


# ── Dispatch ─────────────────────────────────────────────────────────────

_DISPATCH: Dict[str, BundleFn] = {
    "Healthcare":                   _healthcare,
    "Real estate":                  _real_estate,
    "Real estate broker":           _real_estate_broker,
    "Education":                    _education,
    "Tutoring / coaching":          _tutoring,
    "Legal":                        _legal,
    "Ecommerce":                    _ecommerce,
    "Finance":                      _finance,
    "SaaS":                         _saas,
    "Manufacturing":                _manufacturing,
    "Hospitality":                  _hospitality,
    "Restaurant / cafe":            _restaurant,
    "Local services":               _local_services,
    "Beauty / salon / wellness":    _salon,
    "Garment / textile retail":     _garment_retail,
    "Logistics / transport":        _logistics,
    "Construction / contracting":   _construction,
    "Auto repair / garage":         _auto_repair,
    "Photography / event services": _photography,
    "Travel / tour operator":       _travel,
    "Consulting":                   _consulting,
}


def compute_kpis(
    *,
    industry: str,
    pipe: dict,
    tasks: dict,
    invoices: dict,
    crm: dict,
) -> List[KpiTile]:
    """Return the 4-tile KPI strip for the given industry. Always returns
    exactly 4 tiles. Falls through to generic CRM KPIs for unknown
    industries (matches the dashboard's pre-industry-aware behaviour)."""
    fn = _DISPATCH.get((industry or "").strip(), _generic)
    return fn(pipe or {}, tasks or {}, invoices or {}, crm or {})
