"""
Multi-tenant isolation contract.

For every router that exposes a /resource/{id} endpoint, the data layer must
filter by business_id so that user A asking for user B's resource by ID
gets a 404 — never B's data.

This test creates two businesses (`biz-a`, `biz-b`), seeds a record of every
resource type into each, then iterates: every (get / update / delete) call
made against biz-a with biz-b's ID must raise. A single passing 200 here is
a security incident.

This is a *unit-level* contract test against the data modules. The auth
layer's `assert_member` covers the X-Business-Id header-swap attack — see
`test_auth_business_membership` at the bottom for that.
"""
from __future__ import annotations

import importlib
import os
import tempfile

import pytest
from fastapi import HTTPException


# ── Test harness ─────────────────────────────────────────────────────────────
def _fresh(db_path: str):
    """Reload every data module against a clean temp DB."""
    os.environ["DB_PATH"] = db_path
    from config import settings as _s
    importlib.reload(_s)
    from api import crm as _crm
    importlib.reload(_crm)
    from api import tasks as _tasks
    importlib.reload(_tasks)
    from api import invoices as _inv
    importlib.reload(_inv)
    from api import documents as _docs
    importlib.reload(_docs)
    from api import custom_agents as _agents
    importlib.reload(_agents)
    from api import saved_queries as _sq
    importlib.reload(_sq)
    from api import rag_collections as _rc
    importlib.reload(_rc)
    return {
        "crm": _crm, "tasks": _tasks, "invoices": _inv, "documents": _docs,
        "custom_agents": _agents, "saved_queries": _sq, "rag_collections": _rc,
    }


def _seed(mods):
    """Seed biz-a and biz-b with one of each resource. Returns the IDs."""
    crm  = mods["crm"]
    tsk  = mods["tasks"]
    inv  = mods["invoices"]
    sq   = mods["saved_queries"]
    rc   = mods["rag_collections"]
    ca   = mods["custom_agents"]

    seeded = {}
    for biz in ("biz-a", "biz-b"):
        seeded[biz] = {
            "company":  crm.create_company(biz, "u", {"name": f"{biz}-co"})["id"],
            "contact":  crm.create_contact(biz, "u", {"first_name": f"{biz}-name"})["id"],
            "deal":     crm.create_deal(biz, "u", {"name": f"{biz}-deal"})["id"],
            "task":     tsk.create_task(biz, "u", {"title": f"{biz}-task"})["id"],
            "invoice":  inv.create_invoice(biz, "u", {"customer_name": f"{biz}-cust"})["id"],
            # Saved queries — signature is (business_id, data). Sql + name only.
            "saved_query": sq.create_query(biz, {
                "name": f"{biz}-q", "question": "How many sales last month?",
            })["id"],
            # RAG collection takes name as positional, not in a dict.
            "rag_collection": rc.create_collection(biz, f"{biz}-coll")["id"],
            "custom_agent": ca.create_agent(biz, "u", {
                "name": f"{biz}-bot", "goal": "Test goal",
                "interval_minutes": 60,
            })["id"],
        }
        # Interaction needs a contact reference.
        seeded[biz]["interaction"] = crm.create_interaction(biz, "u", {
            "type": "note", "subject": f"{biz}-int", "summary": "x",
            "contact_id": seeded[biz]["contact"],
        })["id"]
    return seeded


# Each entry: (module key, function name, expected exception path).
# We'll call each fn as (biz_a, id_belonging_to_biz_b) and require it to
# raise HTTPException(404). The third tuple element is the kwargs/positional
# argument template; we use a simple tag system to keep things terse.
CROSS_TENANT_LOOKUPS = [
    # (mod, fn_name, kw_argname_for_id, seed_key)
    ("crm",            "get_company",      "company_id",     "company"),
    ("crm",            "update_company",   "company_id",     "company"),
    ("crm",            "delete_company",   "company_id",     "company"),
    ("crm",            "get_contact",      "contact_id",     "contact"),
    ("crm",            "update_contact",   "contact_id",     "contact"),
    ("crm",            "delete_contact",   "contact_id",     "contact"),
    ("crm",            "get_deal",         "deal_id",        "deal"),
    ("crm",            "update_deal",      "deal_id",        "deal"),
    ("crm",            "delete_deal",      "deal_id",        "deal"),
    ("crm",            "get_interaction",  "interaction_id", "interaction"),
    ("crm",            "delete_interaction","interaction_id","interaction"),
    ("tasks",          "get_task",         "task_id",        "task"),
    ("tasks",          "update_task",      "task_id",        "task"),
    ("tasks",          "delete_task",      "task_id",        "task"),
    ("invoices",       "get_invoice",      "invoice_id",     "invoice"),
    ("invoices",       "update_invoice",   "invoice_id",     "invoice"),
    ("invoices",       "delete_invoice",   "invoice_id",     "invoice"),
    ("documents",      "get_document",     "document_id",    None),  # no seed helper; covered separately
    ("custom_agents",  "get_agent",        "agent_id",       "custom_agent"),
    ("custom_agents",  "update_agent",     "agent_id",       "custom_agent"),
    ("custom_agents",  "delete_agent",     "agent_id",       "custom_agent"),
    ("saved_queries",  "get_query",        "query_id",       "saved_query"),
    ("saved_queries",  "update_query",     "query_id",       "saved_query"),
    ("saved_queries",  "delete_query",     "query_id",       "saved_query"),
    ("rag_collections","delete_collection","collection_id",  "rag_collection"),
]


def _call_cross_tenant(mods, mod_key, fn_name, id_value):
    """Invoke fn as (biz-a, biz-b's id, ...) with placeholder updates dict."""
    fn = getattr(mods[mod_key], fn_name)
    if fn_name.startswith("get_") or fn_name.startswith("delete_"):
        return fn("biz-a", id_value)
    if fn_name.startswith("update_"):
        return fn("biz-a", id_value, {})
    raise AssertionError(f"Unknown fn convention: {fn_name}")


# ── The contract ─────────────────────────────────────────────────────────────
@pytest.mark.parametrize("mod_key,fn_name,_arg,seed_key", CROSS_TENANT_LOOKUPS)
def test_cross_tenant_resource_access_is_blocked(mod_key, fn_name, _arg, seed_key):
    """biz-a asking for biz-b's resource by ID must raise HTTPException 404."""
    if seed_key is None:
        pytest.skip("No simple seed helper for this resource — covered separately.")

    with tempfile.TemporaryDirectory() as tmp:
        mods = _fresh(os.path.join(tmp, "nexus.db"))
        seeded = _seed(mods)
        biz_b_id = seeded["biz-b"][seed_key]

        with pytest.raises(HTTPException) as exc:
            _call_cross_tenant(mods, mod_key, fn_name, biz_b_id)

        assert exc.value.status_code in (404, 400), (
            f"{mod_key}.{fn_name}(biz-a, biz-b's {seed_key}) must reject — "
            f"got HTTP {exc.value.status_code}: {exc.value.detail}"
        )

        # Sanity-check: biz-b can still fetch its own resource (proving the
        # row isn't gone, just unreachable from biz-a).
        if fn_name.startswith("get_") and seed_key != "rag_collection":
            getter = getattr(mods[mod_key], fn_name)
            row = getter("biz-b", biz_b_id)
            assert row, f"biz-b lost access to its own {seed_key} after the cross-tenant probe"


# ── Documents — seed by direct DB insert (no test-friendly create helper) ───
def test_documents_cross_tenant_blocked():
    import sqlite3
    import uuid
    from datetime import datetime
    with tempfile.TemporaryDirectory() as tmp:
        mods = _fresh(os.path.join(tmp, "nexus.db"))
        docs = mods["documents"]
        # Touch the table init by calling list_documents (lazy schema setup).
        docs.list_documents("biz-warmup")

        from config.settings import DB_PATH
        a_id, b_id = str(uuid.uuid4()), str(uuid.uuid4())
        now = datetime.now(__import__("datetime").timezone.utc).isoformat()
        conn = sqlite3.connect(DB_PATH)
        try:
            for doc_id, biz, title in [(a_id, "biz-a", "A"), (b_id, "biz-b", "B")]:
                conn.execute(
                    f"INSERT INTO {docs.DOCS_TABLE} "
                    "(id, business_id, template_key, title, format, file_path, "
                    " variables, created_at, created_by) "
                    "VALUES (?,?,?,?,?,?,?,?,?)",
                    (doc_id, biz, "seed", title, "pdf", "/tmp/x.pdf",
                     "{}", now, "u"),
                )
            conn.commit()
        finally:
            conn.close()

        with pytest.raises(HTTPException) as exc:
            docs.get_document("biz-a", b_id)
        assert exc.value.status_code == 404

        with pytest.raises(HTTPException) as exc:
            docs.delete_document("biz-a", b_id)
        assert exc.value.status_code == 404

        # biz-b still has its row.
        assert docs.get_document("biz-b", b_id)["id"] == b_id
        # biz-a still has its row.
        assert docs.get_document("biz-a", a_id)["id"] == a_id


# ── Bulk operations should also reject cross-tenant IDs silently ─────────────
def test_bulk_delete_ignores_other_tenant_ids():
    """bulk_delete given a foreign-tenant ID must be a no-op for that row."""
    with tempfile.TemporaryDirectory() as tmp:
        mods = _fresh(os.path.join(tmp, "nexus.db"))
        crm = mods["crm"]
        tsk = mods["tasks"]
        inv = mods["invoices"]

        a = crm.create_contact("biz-a", "u", {"first_name": "A"})["id"]
        b = crm.create_contact("biz-b", "u", {"first_name": "B"})["id"]
        # biz-a tries to delete biz-b's contact via bulk — must affect 0 rows.
        assert crm.bulk_delete_contacts("biz-a", [b]) == 0
        # biz-b's row is intact.
        assert crm.get_contact("biz-b", b)["first_name"] == "B"

        # Same for tasks
        ta = tsk.create_task("biz-a", "u", {"title": "TA"})["id"]
        tb = tsk.create_task("biz-b", "u", {"title": "TB"})["id"]
        assert tsk.bulk_delete("biz-a", [tb]) == 0
        assert tsk.get_task("biz-b", tb)["title"] == "TB"
        _ = ta  # silence unused-warning lint

        # Invoices
        ia = inv.create_invoice("biz-a", "u", {"customer_name": "IA"})["id"]
        ib = inv.create_invoice("biz-b", "u", {"customer_name": "IB"})["id"]
        assert inv.bulk_delete_invoices("biz-a", [ib]) == 0
        assert inv.get_invoice("biz-b", ib)["customer_name"] == "IB"
        _ = ia


# ── Auth-layer contract — X-Business-Id header swap is rejected ──────────────
def test_assert_member_rejects_non_member():
    """User A holding a valid JWT but sending biz-B's id in the header must fail."""
    with tempfile.TemporaryDirectory() as tmp:
        os.environ["DB_PATH"] = os.path.join(tmp, "nexus.db")
        from config import settings as _s
        importlib.reload(_s)
        from api import businesses as _biz
        importlib.reload(_biz)

        # User A owns biz-a; user B owns biz-b. They've never been members of
        # each other's businesses — the data layer enforces this.
        _biz.create_business("user-a", "Alpha Co")
        biz_b_id = _biz.create_business("user-b", "Bravo Co")["id"]

        # User A is not a member of biz-b. assert_member must raise 403.
        with pytest.raises(HTTPException) as exc:
            _biz.assert_member(biz_b_id, "user-a")
        assert exc.value.status_code == 403, (
            f"assert_member(biz_b, user_a) must return 403 — got {exc.value.status_code}: "
            f"{exc.value.detail}. This is the X-Business-Id header-swap defence."
        )


# ── Listing endpoints must scope by business_id ──────────────────────────────
def test_list_endpoints_dont_leak():
    """Listing as biz-a must never include biz-b's records."""
    with tempfile.TemporaryDirectory() as tmp:
        mods = _fresh(os.path.join(tmp, "nexus.db"))
        seeded = _seed(mods)
        crm = mods["crm"]
        tsk = mods["tasks"]
        inv = mods["invoices"]
        sq  = mods["saved_queries"]
        ca  = mods["custom_agents"]

        # All of biz-b's seeded IDs:
        b_ids = set(seeded["biz-b"].values())

        listings = {
            "contacts":  [c["id"] for c in crm.list_contacts("biz-a", limit=500)],
            "companies": [c["id"] for c in crm.list_companies("biz-a", limit=500)],
            "deals":     [d["id"] for d in crm.list_deals("biz-a", limit=500)],
            "tasks":     [t["id"] for t in tsk.list_tasks("biz-a", limit=500)],
            "invoices":  [i["id"] for i in inv.list_invoices("biz-a", limit=500)],
            "saved_queries": [q["id"] for q in sq.list_queries("biz-a")],
            "custom_agents": [a["id"] for a in ca.list_agents("biz-a")],
        }
        for entity, ids in listings.items():
            leaked = b_ids.intersection(ids)
            assert not leaked, f"{entity} list for biz-a leaked biz-b ids: {leaked}"
