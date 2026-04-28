-- 0003 — Ideal Customer Profile + lead scoring.
--
-- nexus_workspace_settings   one row per business; holds the ICP description
--                            the user defined in Settings. Future workspace-
--                            scoped knobs that don't fit on nexus_businesses
--                            land here too.
--
-- The lead_score / lead_score_reason / lead_scored_at columns live on
-- nexus_contacts. Like the `source` column from migration 0002, those are
-- ensured at runtime in api.crm._get_conn (see comment in that file) so
-- they survive both fresh-installs and existing workspaces without any
-- ordering risk against the lazy schema-init pattern.

CREATE TABLE IF NOT EXISTS nexus_workspace_settings (
    business_id        TEXT PRIMARY KEY,
    icp_description    TEXT DEFAULT '',
    icp_updated_at     TEXT,
    icp_updated_by     TEXT
);
