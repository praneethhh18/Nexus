-- 0008 -- GST split + UPI deep-link columns on nexus_invoices.
--        Also GST billing-profile columns on nexus_businesses.
--
-- These columns are also added by the inline _get_conn() migration inside
-- api/invoices.py (additive ALTER TABLE loop), so this migration acts as
-- the canonical written record for Postgres / CI environments.
--
-- Safe to run multiple times — all statements use IF NOT EXISTS / IGNORE
-- patterns via the app migration runner.

-- ── nexus_invoices — GST split fields ────────────────────────────────────────
ALTER TABLE nexus_invoices ADD COLUMN IF NOT EXISTS igst_amount    REAL DEFAULT 0;
ALTER TABLE nexus_invoices ADD COLUMN IF NOT EXISTS cgst_amount    REAL DEFAULT 0;
ALTER TABLE nexus_invoices ADD COLUMN IF NOT EXISTS sgst_amount    REAL DEFAULT 0;
ALTER TABLE nexus_invoices ADD COLUMN IF NOT EXISTS place_of_supply TEXT DEFAULT '';
ALTER TABLE nexus_invoices ADD COLUMN IF NOT EXISTS upi_link        TEXT DEFAULT '';

-- ── nexus_businesses — India billing profile ──────────────────────────────────
-- gstin / state_code were used at invoice-create time to compute the GST split;
-- default_gst_rate controls the slab applied when a line item omits gst_rate.
ALTER TABLE nexus_businesses ADD COLUMN IF NOT EXISTS gstin            TEXT DEFAULT '';
ALTER TABLE nexus_businesses ADD COLUMN IF NOT EXISTS state_code       TEXT DEFAULT '';
ALTER TABLE nexus_businesses ADD COLUMN IF NOT EXISTS upi_vpa          TEXT DEFAULT '';
ALTER TABLE nexus_businesses ADD COLUMN IF NOT EXISTS default_gst_rate REAL DEFAULT 18;
