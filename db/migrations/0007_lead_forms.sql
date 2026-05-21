-- 0007 -- hosted lead-capture forms.
--
-- Each form is a user-built collection of fields with a public URL like
-- /f/<slug>. Submissions go to /api/public/leads using the forms bound
-- intake key, with the form slug + optional channel tag (via=whatsapp etc.)
-- captured for attribution.

CREATE TABLE IF NOT EXISTS nexus_lead_forms (
    id              TEXT PRIMARY KEY,
    business_id     TEXT NOT NULL,
    slug            TEXT NOT NULL,             -- URL slug, unique per business
    intake_key_id   TEXT NOT NULL,             -- FK → nexus_intake_keys.id
    title           TEXT NOT NULL,
    description     TEXT DEFAULT '',
    fields_json     TEXT NOT NULL DEFAULT '[]',-- JSON array of field defs
    thank_you       TEXT DEFAULT '',           -- message shown after submit
    accent_color    TEXT DEFAULT '#8b5cf6',
    submit_count    INTEGER DEFAULT 0,
    created_at      TEXT NOT NULL,
    created_by      TEXT NOT NULL,
    archived_at     TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_lead_forms_biz_slug
    ON nexus_lead_forms(business_id, slug);
CREATE INDEX IF NOT EXISTS idx_lead_forms_biz ON nexus_lead_forms(business_id);

-- Track per-submission channel attribution. Lives separately from
-- nexus_contacts because a single contact (deduped) may have many
-- submissions across different forms / channels.
CREATE TABLE IF NOT EXISTS nexus_lead_form_submissions (
    id            TEXT PRIMARY KEY,
    business_id   TEXT NOT NULL,
    form_id       TEXT NOT NULL,
    contact_id    TEXT NOT NULL,
    channel       TEXT DEFAULT '',             -- via tag from URL params, e.g. whatsapp
    created_at    TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_lead_form_sub_form    ON nexus_lead_form_submissions(form_id);
CREATE INDEX IF NOT EXISTS idx_lead_form_sub_contact ON nexus_lead_form_submissions(contact_id);
CREATE INDEX IF NOT EXISTS idx_lead_form_sub_biz     ON nexus_lead_form_submissions(business_id);
