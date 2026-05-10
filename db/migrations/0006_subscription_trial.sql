-- 0006_subscription_trial.sql — 14-day trial state on subscriptions.
--
-- Adds two timestamp columns + a "trial" status code to nexus_subscriptions.
-- The plan field stays as 'pro' (or whatever tier we're trialling); status
-- distinguishes trial-grant from paid-active. Plan-gating treats 'trial'
-- as active so the user gets the full Pro experience.
--
-- Lifecycle:
--   signup           → plan='pro',    status='trial',     trial_*=set
--   pay before end   → plan='pro',    status='active',    trial_* preserved
--   end (no pay)     → plan='free',   status='active'     (reaped daily)
--
-- Backwards-compatible: any existing rows with status='active' stay
-- active; the trial columns just stay NULL for them.

ALTER TABLE nexus_subscriptions ADD COLUMN trial_started_at TEXT;
ALTER TABLE nexus_subscriptions ADD COLUMN trial_ends_at    TEXT;

-- Plain index — trial_ends_at is null for non-trial rows but the index
-- is small (one row per business) so a partial index isn't worth the
-- backend-flavour difference between SQLite and Postgres syntax.
CREATE INDEX IF NOT EXISTS idx_subs_trial_ends
    ON nexus_subscriptions(trial_ends_at);
