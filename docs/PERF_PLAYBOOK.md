# Performance Playbook

Why dev feels slow and what production looks like, with the levers to pull.

## The model

A request through this app does roughly:

```
Browser → CDN (frontend) → API → middleware (5 DB queries) → endpoint (1-5 DB queries) → response
```

The dominant cost on small endpoints (most of the dashboard) is **DB round-trip latency × number of queries**, not CPU.

### Dev cost breakdown (typical)

| Stage                        | Time (dev, remote PG) | Time (prod, same-VPC) |
|------------------------------|----------------------:|----------------------:|
| TLS handshake (per-conn)     |         100-200 ms    |               1-3 ms  |
| Session check query          |         100-150 ms    |               1-2 ms  |
| Session touch UPDATE         |         100-150 ms    |               1-2 ms  |
| User lookup query            |         100-150 ms    |               1-2 ms  |
| Business membership lookup   |         100-150 ms    |               1-2 ms  |
| Endpoint work                |         varies        |               varies  |
| **Baseline overhead**        |     **500-800 ms**    |          **5-15 ms**  |

Production is **~50-100× faster** for the same code — purely because the DB lives next to the API.

## What's already wired in this repo

| Fix                                           | Where                                     | Status |
|-----------------------------------------------|-------------------------------------------|:------:|
| `/api/health` 60s in-process cache            | `api/server.py`                           | ✅     |
| Dashboard two-tier loading                    | `frontend/src/pages/Dashboard.jsx`        | ✅     |
| `touch_session` throttle (60s per jti)        | `api/security.py`                         | ✅     |
| Postgres connection pool (opt-in)             | `config/db.py`                            | ✅     |
| 25 DB indexes auto-applied at boot            | `api/db_indexes.py`                       | ✅     |
| CORS + gzip middleware                        | `api/server.py`                           | ✅     |
| Lazy route chunks (frontend)                  | `frontend/src/App.jsx`                    | ✅     |
| Skeletons during first paint                  | `frontend/src/components/Skeleton.jsx`    | ✅     |

## Production deployment checklist (perf-critical bits)

### 1. Co-locate API and DB

Put the API server and the Postgres instance in the **same AWS region + same VPC** (or use a managed DB inside the same provider). Cross-region or DB-on-laptop adds 50-200ms per query and there is no way to fix that with code.

### 2. Enable the connection pool

In production env vars:

```bash
POSTGRES_POOL_ENABLED=1
POSTGRES_POOL_MIN=5    # default 2 — bump for higher traffic
POSTGRES_POOL_MAX=20   # default 10 — stay under DB's max_connections / 2
```

**Important:** the pool only works with a stable worker process. Do **not** run `uvicorn --reload` in production. Use one of:

```bash
# Single worker (small instance, low traffic)
uvicorn api.server:app --host 0.0.0.0 --port 8000

# Multiple workers (recommended for any real traffic)
gunicorn -w 4 -k uvicorn.workers.UvicornWorker api.server:app --bind 0.0.0.0:8000
```

Each gunicorn worker gets its own pool. With 4 workers × max_size=10 = 40 max DB connections — stay under your managed-PG limit.

### 3. Frontend on a CDN

Deploy `frontend/dist/` to Vercel, Cloudflare Pages, or Netlify. All three:
- Serve from edge nodes globally (< 50ms to most users)
- Auto-gzip + brotli (cuts bundle size ~70%)
- Cache hashed assets immutably (browser never re-downloads)

This handles the **bundle-download time** that's currently 1-3s in dev.

### 4. SPA fallback for routes

For Vercel, this is already in `landing/vercel.json` and should be added to `frontend/`:

```json
{ "rewrites": [{ "source": "/((?!api|assets|.*\\..*).*)",  "destination": "/index.html" }] }
```

Without this, hard-refresh on `/dashboard`, `/agents`, etc. 404s.

### 5. Set `APP_BASE_URL` correctly

Verification email links + Razorpay return URLs are built from `APP_BASE_URL`:

```bash
APP_BASE_URL=https://app.nexusagent.in
```

Wrong value → users click "verify" and land in `localhost:5173` or a dead host.

### 6. Sentry sampling

`tracesSampleRate: 0.1` in `frontend/src/main.jsx` is already set. Consider also:

```bash
SENTRY_DSN=...
SENTRY_TRACES_SAMPLE_RATE=0.05   # backend — 5% under load
```

Tracing every request adds ~5-20ms per request at high volume. Sampling keeps tail latency clean.

### 7. Disable `--reload` and verbose loguru in prod

```bash
LOGURU_LEVEL=INFO        # WARNING for production at scale
```

`loguru.logger.debug(...)` is cheap, but writing 50 lines to stdout per request still costs.

## What to watch in production

Add these dashboards / alerts:

| Metric                       | Target              | Where                           |
|------------------------------|---------------------|---------------------------------|
| API p95 latency              | < 300 ms            | Sentry Performance              |
| DB connection-pool exhausted | 0 events / hr       | `psycopg_pool` exposes stats    |
| `/api/health` 5xx rate       | 0                   | Uptime monitor (Better Stack)   |
| LLM provider error rate      | < 1%                | Sentry → tag `provider`         |
| Frontend bundle size         | < 250 KB initial    | Vite build output               |

## Slow-path triage

If a specific endpoint is slow in production:

1. **Check the SQL it runs** — `EXPLAIN ANALYZE` from psql. Missing index?
2. **Check round-trip count** — does it make 1 query or 10? Look for N+1 patterns.
3. **Check LLM calls** — `briefingRun`, agent endpoints, etc. take 10-30s; they should be async (background scheduler) not in the request path.

Most slow endpoints in this codebase are either:
- LLM-in-request-path (briefing, voice, chat) — move to background where possible
- N+1 SELECTs (typically when fetching deals + their stages or contacts + their companies) — fix with a JOIN

## What NOT to chase

These won't help materially given the current shape of the app:

- **Redis cache** — premature. The dashboard summary is small; an in-process LRU is enough.
- **Service-worker offline cache** — adds complexity; users will be online for SaaS anyway.
- **Edge functions for API** — current API is stateful (connection pool, scheduler); won't fit edge runtimes cleanly.
- **Server-side rendering** — the SPA bundle is already split per-route; SSR has high engineering cost for marginal first-paint win.

## Single biggest deployment win

Same-VPC DB + connection pool. Everything else is < 2× speedups; that one is **50-100×**.
