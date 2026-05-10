#!/usr/bin/env bash
# Nightly DB backup — Postgres dump + SQLite copy → S3 (or any compatible
# object store). Run from cron at 03:00 server time.
#
# Cron line on the prod box (one example):
#   0 3 * * * /home/ubuntu/NexusAgent/scripts/backup_db.sh >> /var/log/nexus-backup.log 2>&1
#
# Required env (set in /etc/nexusagent.env or the cron's environment):
#   BACKUP_S3_BUCKET   e.g. s3://nexusagent-backups
#   AWS_REGION         e.g. ap-south-1
#   AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY  (or use IAM role on EC2)
#
# Optional:
#   DATABASE_URL       Postgres URL (postgresql://user:pass@host/db)
#   DB_PATH            SQLite file path (default: ./data/nexusagent.db)
#   BACKUP_RETAIN_DAYS Keep this many daily backups in S3 (default 14)
#
# What it does:
#   1. Either pg_dump or sqlite3 .backup, gzip the result
#   2. Upload to s3://${BACKUP_S3_BUCKET}/YYYY-MM-DD/db.sql.gz
#   3. Prune backups older than BACKUP_RETAIN_DAYS days (S3 lifecycle is
#      cleaner long-term, but this works without IAM policy setup).

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DATE=$(date -u +%Y-%m-%d)
TS=$(date -u +%H%M%S)
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

OUT="$TMP/db-${TS}.sql"
GZ="$OUT.gz"

# ── Dump: Postgres or SQLite ──────────────────────────────────────────────
if [[ -n "${DATABASE_URL:-}" ]] && [[ "$DATABASE_URL" == postgres* ]]; then
  echo "[backup] pg_dump -> $OUT"
  pg_dump --no-owner --no-acl --clean --if-exists "$DATABASE_URL" > "$OUT"
else
  DB_FILE="${DB_PATH:-$ROOT/data/nexusagent.db}"
  if [[ ! -f "$DB_FILE" ]]; then
    echo "[backup] ERROR: DB file not found: $DB_FILE"
    exit 2
  fi
  echo "[backup] sqlite3 .backup $DB_FILE -> $OUT"
  # .backup is hot-safe (works while the DB is being written to)
  sqlite3 "$DB_FILE" ".backup '$OUT'"
fi

gzip -9 "$OUT"
SIZE=$(du -h "$GZ" | cut -f1)
echo "[backup] compressed: $GZ ($SIZE)"

# ── Upload ────────────────────────────────────────────────────────────────
if [[ -z "${BACKUP_S3_BUCKET:-}" ]]; then
  echo "[backup] BACKUP_S3_BUCKET not set — keeping local copy at $GZ"
  cp "$GZ" "$ROOT/backups/db-${DATE}-${TS}.sql.gz"
  exit 0
fi

KEY="${BACKUP_S3_BUCKET%/}/${DATE}/db-${TS}.sql.gz"
echo "[backup] aws s3 cp $GZ $KEY"
aws s3 cp "$GZ" "$KEY" --no-progress

# ── Retention ─────────────────────────────────────────────────────────────
RETAIN_DAYS="${BACKUP_RETAIN_DAYS:-14}"
CUTOFF=$(date -u -d "$RETAIN_DAYS days ago" +%Y-%m-%d 2>/dev/null || \
         date -u -v-"${RETAIN_DAYS}d" +%Y-%m-%d)   # Linux + BSD/macOS
echo "[backup] pruning backups older than $CUTOFF"
aws s3 ls "${BACKUP_S3_BUCKET%/}/" | awk '{print $2}' | sed 's:/$::' | \
  while read -r d; do
    [[ "$d" < "$CUTOFF" ]] && {
      echo "[backup]   prune $d"
      aws s3 rm "${BACKUP_S3_BUCKET%/}/$d/" --recursive --quiet
    }
  done

echo "[backup] done"
