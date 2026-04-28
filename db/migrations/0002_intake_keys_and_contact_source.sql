-- 0002 — public lead capture infrastructure.
--
-- Adds the nexus_intake_keys table that holds revocable per-workspace
-- keys used by the public POST /api/public/leads endpoint.
--
-- The companion `source` column on nexus_contacts is added at runtime
-- by api.crm._get_conn (see the additive-migration pattern in
-- api/invoices.py for precedent) — this avoids ordering issues where
-- this migration would run before crm.py has lazily created the
-- contacts table on first use.

CREATE TABLE IF NOT EXISTS nexus_intake_keys (
    id           TEXT PRIMARY KEY,
    business_id  TEXT NOT NULL,
    key_hash     TEXT NOT NULL,        -- sha-256 of the actual key; raw never stored
    key_prefix   TEXT NOT NULL,        -- first 8 chars, for display ("nx_pub_a1b2…")
    label        TEXT DEFAULT '',      -- "homepage form", "footer signup", etc.
    created_at   TEXT NOT NULL,
    created_by   TEXT NOT NULL,
    revoked_at   TEXT,
    last_used_at TEXT,
    use_count    INTEGER DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_intake_keys_biz ON nexus_intake_keys(business_id);
CREATE INDEX IF NOT EXISTS idx_intake_keys_hash ON nexus_intake_keys(key_hash);
