"""
CRM dedup guard — contract tests.

Behavior under test (`agents/tools/crm_tools.py::_create_contact|_create_company`):

  1. Creating a contact with a fresh email → real create.
  2. Creating "the same" contact with the SAME email → returns existing (duplicate).
  3. Creating "the same" contact with NEW phone → updates existing, fills phone.
  4. Existing email NEVER gets overwritten by a create call (must use update_contact).
  5. Same-name match works when no email present on either side.
  6. "Rajesh" doesn't accidentally match "Rajesh Kumar" — first-name-only is strict.
  7. Companies dedup by exact name (case + whitespace insensitive).
"""
from __future__ import annotations

import importlib
import os
import tempfile

import pytest


@pytest.fixture
def fresh(tmp_path, monkeypatch):
    """Per-test SQLite. Reload only crm (not crm_tools — it registers tools
    on import and re-registration would error)."""
    db = str(tmp_path / "nexus.db")
    monkeypatch.setenv("DB_PATH", db)
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    # Import crm_tools after crm is reloaded; the in-place reload means any
    # already-imported reference inside crm_tools picks up the new DB.
    from agents.tools import crm_tools as _ct
    return _crm, _ct


def _ctx(business_id="biz-a"):
    return {"business_id": business_id, "user_id": "u-1"}


def test_fresh_create_makes_a_new_contact(fresh):
    crm, ct = fresh
    out = ct._create_contact(_ctx(), {"first_name": "Sita", "email": "sita@example.com"})
    assert out["email"] == "sita@example.com"
    assert "_dedup" not in out  # fresh create has no dedup marker


def test_same_email_returns_existing_as_duplicate(fresh):
    crm, ct = fresh
    ct._create_contact(_ctx(), {"first_name": "Sita", "email": "sita@example.com"})
    out = ct._create_contact(_ctx(), {"first_name": "Sita", "email": "Sita@Example.COM"})
    assert out["_dedup"] == "duplicate"
    # Confirm only ONE row in DB
    rows = crm.list_contacts("biz-a")
    assert len(rows) == 1


def test_new_field_merges_into_existing(fresh):
    crm, ct = fresh
    ct._create_contact(_ctx(), {"first_name": "Sita", "email": "sita@example.com"})
    out = ct._create_contact(_ctx(), {"first_name": "Sita", "email": "sita@example.com",
                                       "phone": "9999000011"})
    assert out["_dedup"] == "merged"
    assert out["phone"] == "9999000011"
    rows = crm.list_contacts("biz-a")
    assert len(rows) == 1


def test_existing_email_not_overwritten_by_create(fresh):
    """Authoritative fields are protected: a create call won't change an
    already-set email. Use update_contact for that."""
    crm, ct = fresh
    ct._create_contact(_ctx(), {"first_name": "Sita", "email": "old@example.com"})
    out = ct._create_contact(_ctx(), {"first_name": "Sita", "email": "old@example.com",
                                       "phone": "111", "title": "CEO"})
    # phone was empty before — gets filled. title same.
    rows = crm.list_contacts("biz-a")
    assert len(rows) == 1
    assert rows[0]["email"] == "old@example.com"
    assert rows[0]["phone"] == "111"
    assert rows[0]["title"] == "CEO"


def test_phone_match_finds_existing(fresh):
    """User adds Rajesh by phone, then later adds 'his email'. The email
    create call must find Rajesh by his existing phone and merge."""
    crm, ct = fresh
    ct._create_contact(_ctx(), {"first_name": "Rajesh", "phone": "9876543210"})
    out = ct._create_contact(_ctx(), {"first_name": "Rajesh", "phone": "9876543210",
                                       "email": "rajeshraj@gmail.com"})
    assert out["_dedup"] == "merged"
    assert out["email"] == "rajeshraj@gmail.com"
    rows = crm.list_contacts("biz-a")
    assert len(rows) == 1


def test_phone_match_normalizes_formatting(fresh):
    crm, ct = fresh
    ct._create_contact(_ctx(), {"first_name": "Rajesh", "phone": "9876543210"})
    out = ct._create_contact(_ctx(), {"first_name": "Rajesh", "phone": "+91-98765-43210",
                                       "email": "r@example.com"})
    # Different format, same digits → same contact.
    assert out["_dedup"] == "merged"
    assert crm.list_contacts("biz-a").__len__() == 1


def test_first_name_only_strict_match(fresh):
    """A 'Rajesh' (no last name) create should NOT match an existing 'Rajesh
    Kumar' — that would silently merge two different people."""
    crm, ct = fresh
    ct._create_contact(_ctx(), {"first_name": "Rajesh", "last_name": "Kumar"})
    out = ct._create_contact(_ctx(), {"first_name": "Rajesh"})
    # Should be a NEW contact, not a merge.
    assert "_dedup" not in out
    rows = crm.list_contacts("biz-a")
    assert len(rows) == 2


def test_full_name_match_dedupes(fresh):
    crm, ct = fresh
    ct._create_contact(_ctx(), {"first_name": "Rajesh", "last_name": "Kumar"})
    out = ct._create_contact(_ctx(), {"first_name": "Rajesh", "last_name": "Kumar",
                                       "email": "rk@x.com"})
    assert out["_dedup"] == "merged"
    rows = crm.list_contacts("biz-a")
    assert len(rows) == 1
    assert rows[0]["email"] == "rk@x.com"


def test_company_dedup_by_name(fresh):
    crm, ct = fresh
    ct._create_company(_ctx(), {"name": "Acme Corp"})
    out = ct._create_company(_ctx(), {"name": "  Acme Corp  ", "industry": "SaaS"})
    assert out["_dedup"] == "merged"
    assert out["industry"] == "SaaS"
    rows = crm.list_companies("biz-a")
    assert len(rows) == 1


def test_dedup_is_per_business(fresh):
    """Business A's Sita doesn't match business B's Sita."""
    crm, ct = fresh
    ct._create_contact({"business_id": "biz-a", "user_id": "u"},
                       {"first_name": "Sita", "email": "sita@example.com"})
    out = ct._create_contact({"business_id": "biz-b", "user_id": "u"},
                             {"first_name": "Sita", "email": "sita@example.com"})
    # Fresh create in biz-b
    assert "_dedup" not in out
    assert len(crm.list_contacts("biz-a")) == 1
    assert len(crm.list_contacts("biz-b")) == 1
