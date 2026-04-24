"""Tests for CRM bulk, invoice bulk + recurrence, entity import, and activity feed."""
from __future__ import annotations

import csv
import importlib
import io
import os
import tempfile


def _fresh(db_path: str):
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    from api import invoices as _inv
    importlib.reload(_inv)
    from api import tasks as _tasks
    importlib.reload(_tasks)
    from api import tags as _tags
    importlib.reload(_tags)
    from api import entity_import as _ei
    importlib.reload(_ei)
    from api import activity_feed as _af
    importlib.reload(_af)
    return _crm, _inv, _tasks, _tags, _ei, _af


# ── CRM bulk ────────────────────────────────────────────────────────────────
def test_bulk_delete_contacts_scoped_to_business():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        a = crm.create_contact("biz-a", "u", {"first_name": "Alice"})
        b = crm.create_contact("biz-b", "u", {"first_name": "Bob"})
        # Deleting biz-a with biz-b id must be a no-op
        assert crm.bulk_delete_contacts("biz-a", [b["id"]]) == 0
        assert crm.get_contact("biz-b", b["id"])["first_name"] == "Bob"
        assert crm.bulk_delete_contacts("biz-a", [a["id"]]) == 1


def test_bulk_delete_companies_nulls_out_fks():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        co = crm.create_company("biz-1", "u", {"name": "Acme"})
        ct = crm.create_contact("biz-1", "u", {"first_name": "A", "company_id": co["id"]})
        d = crm.create_deal("biz-1", "u", {"name": "D", "company_id": co["id"]})
        crm.bulk_delete_companies("biz-1", [co["id"]])
        # Contact and deal survive with null FK
        assert crm.get_contact("biz-1", ct["id"])["company_id"] is None
        assert crm.get_deal("biz-1", d["id"])["company_id"] is None


def test_bulk_update_deal_stage_rejects_invalid():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        d = crm.create_deal("biz-1", "u", {"name": "D"})
        import pytest
        from fastapi import HTTPException
        with pytest.raises(HTTPException):
            crm.bulk_update_deal_stage("biz-1", [d["id"]], "not_a_stage")


def test_bulk_update_deal_stage_updates_many():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        ids = [crm.create_deal("biz-1", "u", {"name": f"D{i}"})["id"] for i in range(3)]
        n = crm.bulk_update_deal_stage("biz-1", ids, "won")
        assert n == 3
        for did in ids:
            assert crm.get_deal("biz-1", did)["stage"] == "won"


# ── Invoice bulk + recurring ────────────────────────────────────────────────
def test_bulk_delete_invoices():
    with tempfile.TemporaryDirectory() as tmp:
        _, inv, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        ids = [inv.create_invoice("biz-1", "u", {"customer_name": f"C{i}"})["id"] for i in range(3)]
        assert inv.bulk_delete_invoices("biz-1", ids[:2]) == 2
        remaining = inv.list_invoices("biz-1", limit=100)
        assert len(remaining) == 1


def test_bulk_update_invoice_status():
    with tempfile.TemporaryDirectory() as tmp:
        _, inv, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        ids = [inv.create_invoice("biz-1", "u", {"customer_name": f"C{i}"})["id"] for i in range(2)]
        n = inv.bulk_update_invoice_status("biz-1", ids, "sent")
        assert n == 2
        for iid in ids:
            assert inv.get_invoice("biz-1", iid)["status"] == "sent"


def test_recurring_invoice_spawns_next_on_paid():
    with tempfile.TemporaryDirectory() as tmp:
        _, inv, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        i = inv.create_invoice("biz-1", "u", {
            "customer_name": "Acme",
            "recurrence": "monthly",
            "issue_date": "2026-01-05",
            "due_date": "2026-02-05",
            "line_items": [{"description": "Retainer", "quantity": 1, "unit_price": 1000}],
        })
        inv.update_invoice("biz-1", i["id"], {"status": "paid"})
        all_invs = inv.list_invoices("biz-1", limit=100)
        # Original + draft next occurrence
        assert len(all_invs) == 2
        draft = [x for x in all_invs if x["status"] == "draft"][0]
        assert draft["recurrence"] == "monthly"
        assert draft["issue_date"] == "2026-02-04"  # +30 days


def test_non_recurring_invoice_does_not_spawn():
    with tempfile.TemporaryDirectory() as tmp:
        _, inv, _, _, _, _ = _fresh(os.path.join(tmp, "nexus.db"))
        i = inv.create_invoice("biz-1", "u", {
            "customer_name": "Acme",
            "issue_date": "2026-01-05",
        })
        inv.update_invoice("biz-1", i["id"], {"status": "paid"})
        assert len(inv.list_invoices("biz-1", limit=100)) == 1


# ── Entity import ───────────────────────────────────────────────────────────
def _write_csv(tmpdir: str, rows, filename="in.csv") -> str:
    path = os.path.join(tmpdir, filename)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        for r in rows:
            w.writerow(r)
    return path


def test_entity_import_preview_auto_maps_contacts():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, ei, _ = _fresh(os.path.join(tmp, "nexus.db"))
        path = _write_csv(tmp, [
            ["First Name", "Last Name", "Email", "Mobile"],
            ["Alice", "Anand", "a@x.com", "+91 98 00 11 22 33"],
            ["Bob", "Bose", "b@x.com", ""],
        ])
        preview = ei.preview(path, "contact")
        assert preview["entity_type"] == "contact"
        assert preview["total_rows"] == 2
        # Suggested mapping should pick obvious columns
        m = preview["suggested_mapping"]
        assert m.get("first_name") == "First Name"
        assert m.get("last_name") == "Last Name"
        assert m.get("email") == "Email"
        # 'Mobile' should alias to phone
        assert m.get("phone") == "Mobile"


def test_entity_import_commit_inserts_contacts():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, _, ei, _ = _fresh(os.path.join(tmp, "nexus.db"))
        path = _write_csv(tmp, [
            ["first_name", "email"],
            ["Alice", "a@x.com"],
            ["Bob",   "b@x.com"],
        ])
        result = ei.commit("biz-1", "user-1", path, "contact", {
            "first_name": "first_name",
            "email": "email",
        })
        assert result["inserted"] == 2
        assert result["skipped"] == 0
        contacts = crm.list_contacts("biz-1")
        assert len(contacts) == 2


def test_entity_import_missing_required_raises():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, ei, _ = _fresh(os.path.join(tmp, "nexus.db"))
        path = _write_csv(tmp, [["email"], ["a@x.com"]])
        import pytest
        with pytest.raises(ValueError):
            ei.commit("biz-1", "u", path, "contact", {"email": "email"})


def test_entity_import_skips_bad_rows_not_whole_batch():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, _, _, ei, _ = _fresh(os.path.join(tmp, "nexus.db"))
        path = _write_csv(tmp, [
            ["first_name"],
            ["Alice"],
            [""],          # bad — no name
            ["Charlie"],
        ])
        result = ei.commit("biz-1", "u", path, "contact", {"first_name": "first_name"})
        assert result["inserted"] == 2
        assert result["skipped"] == 1
        assert len(result["errors"]) == 1


# ── Activity feed ───────────────────────────────────────────────────────────
def test_activity_timeline_collects_tag_task_invoice_events():
    with tempfile.TemporaryDirectory() as tmp:
        crm, inv, tasks, tags, _, af = _fresh(os.path.join(tmp, "nexus.db"))

        contact = crm.create_contact("biz-1", "u", {"first_name": "Alice", "email": "a@x.com"})
        tasks.create_task("biz-1", "u", {"title": "Call Alice", "contact_id": contact["id"]})
        inv.create_invoice("biz-1", "u", {
            "customer_name": "Alice", "customer_contact_id": contact["id"],
        })
        tag = tags.create_tag("biz-1", "VIP")
        tags.assign("biz-1", tag["id"], "contact", contact["id"])

        events = af.timeline("biz-1", "contact", contact["id"])
        kinds = [e["kind"] for e in events]
        assert "tag_added" in kinds
        assert "task_created" in kinds
        assert "invoice_created" in kinds


def test_activity_timeline_rejects_unknown_entity_type():
    with tempfile.TemporaryDirectory() as tmp:
        _, _, _, _, _, af = _fresh(os.path.join(tmp, "nexus.db"))
        import pytest
        with pytest.raises(ValueError):
            af.timeline("biz-1", "badtype", "xyz")


def test_activity_timeline_is_scoped_to_entity():
    with tempfile.TemporaryDirectory() as tmp:
        crm, _, tasks, _, _, af = _fresh(os.path.join(tmp, "nexus.db"))
        c1 = crm.create_contact("biz-1", "u", {"first_name": "Alice"})
        c2 = crm.create_contact("biz-1", "u", {"first_name": "Bob"})
        tasks.create_task("biz-1", "u", {"title": "Only Alice", "contact_id": c1["id"]})
        events1 = af.timeline("biz-1", "contact", c1["id"])
        events2 = af.timeline("biz-1", "contact", c2["id"])
        # Alice's timeline has a task event; Bob's doesn't.
        assert any(e["kind"] == "task_created" for e in events1)
        assert not any(e["kind"] == "task_created" for e in events2)
