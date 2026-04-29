# NexusAgent — Deployment Guide

This guide covers taking NexusAgent from local dev to a real server.
Three deployment modes, from simplest to most production-y.

---

## Mode 1 — Local laptop (what you're doing now)

```powershell
# backend + frontend in separate terminals
uvicorn api.server:app --reload --port 8000
cd frontend && npm run dev
```

Fine for one user. Not accessible from outside your laptop. Nothing else needed.

---

## Mode 2 — One VPS, SQLite, Docker

**This is the sweet spot for most users.** A single $5/month DigitalOcean or
Hetzner droplet handles this comfortably. All services in one compose stack.

### Prerequisites

- A Linux VPS (Ubuntu 22.04+ recommended)
- A domain name pointing at it (optional but recommended for HTTPS)
- Docker + Docker Compose installed

```bash
# On the VPS
sudo apt update && sudo apt install -y docker.io docker-compose-plugin curl
sudo systemctl enable --now docker
```

### Deploy

```bash
# Clone your repo onto the server (or rsync from local)
git clone <your-repo-url> nexusagent
cd nexusagent

# Set up .env
cp .env.example .env
nano .env
# Fill in at minimum:
#   JWT_SECRET                (32+ char random string)
#   AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY / AWS_REGION  (for Bedrock)
#   APP_BASE_URL=https://yourdomain.com

# Build frontend once so proxy can serve the static files
docker run --rm -v "$PWD/frontend:/frontend" -w /frontend node:20-slim sh -c "npm ci && npm run build"

# Bring it up
docker compose up -d

# Check health
curl http://localhost/api/health
```

At this point NexusAgent is running on port 80. Visit `http://your-ip/` in a
browser.

### Enable HTTPS

Use Caddy or Certbot + nginx. Easiest — run Caddy in front of port 80:

```bash
docker run -d --name caddy \
  --network host \
  -v caddy_data:/data \
  -v "$PWD/Caddyfile:/etc/caddy/Caddyfile" \
  caddy:latest
```

`Caddyfile`:
```
yourdomain.com {
    reverse_proxy localhost:80
}
```

Caddy auto-acquires a Let's Encrypt cert. Done.

### Enable automated backups

```bash
docker compose --profile backup up -d
```

Creates `backups/nexusagent_YYYYMMDD_HHMMSS.db.gz` daily at 03:00 UTC,
keeps the last 14 days + weekly snapshots for 8 weeks, auto-pruned.

### Enable the WhatsApp bridge

```bash
# First set up the bridge .env
cd whatsapp_bridge
cp .env.example .env
# Fill in NEXUS_WEBHOOK_SECRET (copy from NexusAgent Settings → WhatsApp as admin)
cd ..

# Bring up the bridge
docker compose --profile bridge up -d

# Watch logs — you'll see the QR code once
docker compose logs -f bridge
# Scan with WhatsApp (Linked devices → Link a device)
```

---

## Mode 3 — Postgres backend

Only needed when you want:
- Multiple app servers behind a load balancer
- Point-in-time recovery / streaming replication
- Read replicas
- Hundreds of concurrent writers

**Stop before doing this if your app has one user.** SQLite + WAL handles
more load than you think (Expensify runs on SQLite in production).

### Step A: Bring up Postgres

Edit `.env`:
```
POSTGRES_PASSWORD=your_strong_password_here
DATABASE_URL=postgresql://nexus:your_strong_password_here@postgres:5432/nexusagent
```

```bash
# Bring up just Postgres first
docker compose --profile postgres up -d postgres

# Wait for it to be healthy
docker compose exec postgres pg_isready -U nexus -d nexusagent
```

### Step B: Install psycopg

Edit `requirements.txt` and uncomment the `psycopg[binary]` line. Rebuild:

```bash
docker compose build api
```

### Step C: Migrate the data

```bash
# First, stop the API so SQLite isn't being written to
docker compose stop api

# Dry run — see what would happen
docker compose run --rm api python tools/migrate_to_postgres.py --dry-run

# Do it
docker compose run --rm api python tools/migrate_to_postgres.py

# Start API again with the new DATABASE_URL
docker compose up -d api
```

### Step D: Switch code modules to config.db

**This is the caveat.** All 21 data modules still call `sqlite3.connect(DB_PATH)`
directly, not `config.db.get_conn()`. With `DATABASE_URL=postgres://...` set,
those calls still hit the local SQLite file.

You have two options:

**Option 1 (recommended for now):** Run both — Postgres for big tables, SQLite
for everything else. This is fine for most apps. Only `nexus_audit_log` and
`nexus_conversations` grow quickly; the rest are small.

**Option 2:** Do the full migration of every module. This is a methodical
find-and-replace job — swap `sqlite3.connect(DB_PATH)` → `get_conn()` from
`config.db` in every `_get_conn()` function. ~1 hour of careful edits. Test
each module's endpoints after switching.

Until Option 2 is done, **SQLite remains the active backend**. Postgres is
parked and ready when you need it.

---

## SQLite production tuning (already applied)

When you start the API server, it automatically applies:
- `journal_mode = WAL` — concurrent readers during writes, ~10× write throughput
- `synchronous = NORMAL` — safe with WAL, no full fsync per commit
- `busy_timeout = 10000` — wait 10s on lock contention before failing
- `mmap_size = 128MB` — faster reads via memory mapping
- `foreign_keys = ON` — enforced

You don't need to do anything. If you want to verify:
```bash
docker compose exec api sqlite3 /app/data/nexusagent.db "PRAGMA journal_mode;"
# should return: wal
```

---

## Backups — how to use

```bash
# Take a manual snapshot right now
python tools/backup_db.py

# List backups
python tools/backup_db.py --list

# Restore (stops the server first)
docker compose stop api
python tools/backup_db.py --restore backups/nexusagent_20260424_030000.db.gz
docker compose start api

# Upload backups to S3 (needs AWS creds configured)
python tools/backup_db.py --upload s3://my-bucket/nexusagent-backups
```

---

## Running the WhatsApp bridge as a service

On a VPS, Docker compose handles this. On Windows for dev, use `nssm`:

```powershell
# Download nssm from https://nssm.cc/download
nssm install NexusWhatsAppBridge "C:\Program Files\nodejs\node.exe" "C:\path\to\NexusAgent\whatsapp_bridge\server.js"
nssm set NexusWhatsAppBridge AppDirectory "C:\path\to\NexusAgent\whatsapp_bridge"
nssm set NexusWhatsAppBridge AppStdout "C:\path\to\NexusAgent\whatsapp_bridge\bridge.log"
nssm start NexusWhatsAppBridge
```

Now the bridge restarts with Windows.

---

## Environment checklist for production

Before going live, make sure these are set in `.env`:

- [ ] `JWT_SECRET` — a 32+ character random string (generate with `openssl rand -base64 48`)
- [ ] `APP_BASE_URL` — your public HTTPS URL (used in password reset emails, invite links)
- [ ] `ANTHROPIC_API_KEY` **or** `AWS_ACCESS_KEY_ID`+`AWS_SECRET_ACCESS_KEY`+`AWS_REGION` — so the LLM works
- [ ] `GMAIL_USER` + `GMAIL_APP_PASSWORD` — if you want outgoing emails (invites, invoices, password resets)
- [ ] Admin password changed from default `admin1234`
- [ ] `ANOMALY_THRESHOLD` and `SQL_QUERY_TIMEOUT_SECONDS` reviewed for your data volume
- [ ] HTTPS in front of the app (Caddy / Let's Encrypt / Cloudflare)
- [ ] Daily backups enabled (`docker compose --profile backup up -d`)

---

## Troubleshooting

| Symptom | Check |
|---|---|
| `SQLITE_BUSY` errors | WAL mode should prevent this. Verify: `PRAGMA journal_mode;` = `wal`. If not, restart the API — pragmas reapply on boot. |
| High disk usage | Audit log and conversations grow. Trim with: `sqlite3 data/nexusagent.db "DELETE FROM nexus_audit_log WHERE timestamp < datetime('now','-90 days'); VACUUM;"` |
| Bridge keeps disconnecting | WhatsApp hates multiple active sessions. Don't pair the same phone from two computers. |
| Bedrock: `AccessDeniedException` | Model access not auto-enabled yet. Go to AWS Bedrock console → Playground → pick Nova Pro → send one message. This enables it account-wide. |
| Nginx 502 Bad Gateway | API container crashed. `docker compose logs api` to see why. |
