-- 0005_subscriptions.sql — persist Razorpay subscription state per business.
--
-- Migration rules:
--   * Use SQLite-native syntax. The migration runner's _translate_sql()
--     converts INTEGER PRIMARY KEY AUTOINCREMENT → BIGSERIAL PRIMARY KEY
--     and TEXT timestamps stay portable across both backends.
--
-- Two tables:
--
--   nexus_subscriptions — current state (one row per business).
--     plan         text (free|starter|pro|privacy|business|self_hosted)
--     status       text (active|cancelled|past_due|trial)
--     current_period_end  text — ISO timestamp; when this billing cycle ends
--
--   nexus_subscription_events — append-only audit log. Every paid event
--   (verified payment, webhook callback, refund, cancellation) lands here
--   so we can reconstruct "who paid what when" without trusting Razorpay's
--   dashboard alone.

CREATE TABLE IF NOT EXISTS nexus_subscriptions (
    business_id              TEXT PRIMARY KEY,
    plan                     TEXT NOT NULL DEFAULT 'free',
    status                   TEXT NOT NULL DEFAULT 'active',
    started_at               TEXT,
    current_period_end       TEXT,
    razorpay_customer_id     TEXT,
    razorpay_subscription_id TEXT,
    last_payment_id          TEXT,
    updated_at               TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS nexus_subscription_events (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    business_id         TEXT NOT NULL,
    event_type          TEXT NOT NULL,
    plan                TEXT,
    amount_paise        INTEGER NOT NULL DEFAULT 0,
    razorpay_order_id   TEXT,
    razorpay_payment_id TEXT,
    payload_json        TEXT,
    created_at          TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_sub_events_biz_created
    ON nexus_subscription_events(business_id, created_at DESC);

CREATE INDEX IF NOT EXISTS idx_sub_events_payment
    ON nexus_subscription_events(razorpay_payment_id);
