#!/usr/bin/env bash
# Non-Docker AWS free-tier bootstrap for NexusAgent.
#
# Run this on a fresh Ubuntu EC2 instance after DNS A records point here.
# It installs nginx, certbot, Node, Python deps, Postgres, builds landing and
# product frontend, installs systemd services, and obtains HTTPS certs.
#
# Usage:
#   export REPO_URL="https://github.com/praneethhh18/Nexus.git"
#   export LETSENCRYPT_EMAIL="you@example.com"
#   bash deploy/non-docker/aws-free-tier-bootstrap.sh
#
# Optional env:
#   APP_USER=ubuntu
#   APP_DIR=/opt/nexusagent
#   DB_PASSWORD=<strong password>
#   JWT_SECRET=<strong secret>
#   VOICE_CALLBACK_SECRET=<shared with NexusCaller>
#   WHATSAPP_WEBHOOK_SECRET=<shared with whatsapp_bridge>

set -euo pipefail

APP_USER="${APP_USER:-ubuntu}"
APP_DIR="${APP_DIR:-/opt/nexusagent}"
VOX_DIR="${VOX_DIR:-/opt/nexuscaller-lab}"
REPO_URL="${REPO_URL:-https://github.com/praneethhh18/Nexus.git}"
VOX_REPO_URL="${VOX_REPO_URL:-https://github.com/praneethhh18/NexusCaller-lab.git}"
LETSENCRYPT_EMAIL="${LETSENCRYPT_EMAIL:-}"
SKIP_CERTBOT="${SKIP_CERTBOT:-0}"

ROOT_DOMAIN="nexusagent.in"
PRODUCT_DOMAIN="nexus.nexusagent.in"
VOX_DOMAIN="vox.nexusagent.in"

if [[ "$SKIP_CERTBOT" != "1" && -z "$LETSENCRYPT_EMAIL" ]]; then
  echo "Set LETSENCRYPT_EMAIL before running."
  exit 1
fi

rand_secret() {
  python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
}

DB_PASSWORD="${DB_PASSWORD:-$(rand_secret)}"
JWT_SECRET="${JWT_SECRET:-$(rand_secret)}"
VOICE_CALLBACK_SECRET="${VOICE_CALLBACK_SECRET:-$(rand_secret)}"
WHATSAPP_WEBHOOK_SECRET="${WHATSAPP_WEBHOOK_SECRET:-$(rand_secret)}"

echo "==> Installing packages"
sudo apt update
sudo apt install -y \
  ca-certificates curl gnupg git nginx certbot python3-certbot-nginx \
  python3-venv python3-pip python3-dev build-essential \
  postgresql postgresql-contrib \
  ffmpeg libsndfile1 portaudio19-dev

echo "==> Installing Node.js 22"
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install -y nodejs

echo "==> Preparing application directory"
sudo mkdir -p "$APP_DIR"
sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
sudo chmod -R u+rwX "$APP_DIR"

if [[ ! -d "$APP_DIR/.git" && -z "$(find "$APP_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  sudo -u "$APP_USER" git clone "$REPO_URL" "$APP_DIR"
elif [[ -d "$APP_DIR/.git" ]]; then
  sudo -u "$APP_USER" git -C "$APP_DIR" pull --ff-only
else
  echo "==> Using existing source in $APP_DIR"
fi

echo "==> Preparing NexusCaller directory"
sudo mkdir -p "$VOX_DIR"
sudo chown -R "$APP_USER:$APP_USER" "$VOX_DIR"
sudo chmod -R u+rwX "$VOX_DIR"

if [[ ! -d "$VOX_DIR/.git" && -z "$(find "$VOX_DIR" -mindepth 1 -maxdepth 1 -print -quit)" ]]; then
  sudo -u "$APP_USER" git clone "$VOX_REPO_URL" "$VOX_DIR"
elif [[ -d "$VOX_DIR/.git" ]]; then
  sudo -u "$APP_USER" git -C "$VOX_DIR" pull --ff-only
else
  echo "==> Using existing NexusCaller source in $VOX_DIR"
fi

cd "$APP_DIR"
sudo chown -R "$APP_USER:$APP_USER" "$APP_DIR"
sudo chmod -R u+rwX "$APP_DIR"

echo "==> Creating local Postgres database"
sudo -u postgres psql <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'nexus') THEN
    CREATE USER nexus WITH PASSWORD '${DB_PASSWORD}';
  ELSE
    ALTER USER nexus WITH PASSWORD '${DB_PASSWORD}';
  END IF;
END
\$\$;
SELECT 'CREATE DATABASE nexusagent OWNER nexus'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'nexusagent')\gexec
GRANT ALL PRIVILEGES ON DATABASE nexusagent TO nexus;
SQL

echo "==> Writing production env"
sudo -u "$APP_USER" cp deploy/non-docker/production.env.example .env
sudo -u "$APP_USER" sed -i \
  -e "s|^DATABASE_URL=.*|DATABASE_URL=postgresql://nexus:${DB_PASSWORD}@127.0.0.1:5432/nexusagent|" \
  -e "s|^JWT_SECRET=.*|JWT_SECRET=${JWT_SECRET}|" \
  -e "s|^VOICE_CALLBACK_SECRET=.*|VOICE_CALLBACK_SECRET=${VOICE_CALLBACK_SECRET}|" \
  -e "s|^WHATSAPP_WEBHOOK_SECRET=.*|WHATSAPP_WEBHOOK_SECRET=${WHATSAPP_WEBHOOK_SECRET}|" \
  -e "s|^REQUIRE_EMAIL_VERIFICATION=.*|REQUIRE_EMAIL_VERIFICATION=1|" \
  .env
sudo chmod 600 .env
sudo chown "$APP_USER:$APP_USER" .env

echo "==> Writing NexusCaller env"
if [[ -f "$VOX_DIR/.env.example" && ! -f "$VOX_DIR/.env" ]]; then
  sudo -u "$APP_USER" cp "$VOX_DIR/.env.example" "$VOX_DIR/.env"
elif [[ ! -f "$VOX_DIR/.env" ]]; then
  sudo -u "$APP_USER" touch "$VOX_DIR/.env"
fi
sudo -u "$APP_USER" grep -q '^VOICE_CALLBACK_SECRET=' "$VOX_DIR/.env" || sudo -u "$APP_USER" tee -a "$VOX_DIR/.env" >/dev/null <<<"VOICE_CALLBACK_SECRET="
sudo -u "$APP_USER" grep -q '^NEXUS_PUBLIC_URL=' "$VOX_DIR/.env" || sudo -u "$APP_USER" tee -a "$VOX_DIR/.env" >/dev/null <<<"NEXUS_PUBLIC_URL="
sudo -u "$APP_USER" grep -q '^VOX_PUBLIC_URL=' "$VOX_DIR/.env" || sudo -u "$APP_USER" tee -a "$VOX_DIR/.env" >/dev/null <<<"VOX_PUBLIC_URL="
sudo -u "$APP_USER" sed -i \
  -e "s|^VOICE_CALLBACK_SECRET=.*|VOICE_CALLBACK_SECRET=${VOICE_CALLBACK_SECRET}|" \
  -e "s|^NEXUS_PUBLIC_URL=.*|NEXUS_PUBLIC_URL=https://${PRODUCT_DOMAIN}|" \
  -e "s|^VOX_PUBLIC_URL=.*|VOX_PUBLIC_URL=https://${VOX_DOMAIN}|" \
  "$VOX_DIR/.env"
sudo chmod 600 "$VOX_DIR/.env"
sudo chown "$APP_USER:$APP_USER" "$VOX_DIR/.env"

echo "==> Installing Python dependencies"
sudo -u "$APP_USER" python3 -m venv venv
sudo -u "$APP_USER" ./venv/bin/pip install --upgrade pip
sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.txt

echo "==> Installing NexusCaller Python dependencies"
cd "$VOX_DIR"
sudo -u "$APP_USER" python3 -m venv venv
sudo -u "$APP_USER" ./venv/bin/pip install --upgrade pip
if [[ -f requirements.txt ]]; then
  sudo -u "$APP_USER" ./venv/bin/pip install -r requirements.txt
fi

echo "==> Applying migrations"
cd "$APP_DIR"
sudo -u "$APP_USER" ./venv/bin/python -m db.migrate

echo "==> Building landing"
cd "$APP_DIR/landing"
sudo -u "$APP_USER" npm ci || sudo -u "$APP_USER" npm install
sudo -u "$APP_USER" npm run build

echo "==> Building product frontend"
cd "$APP_DIR/frontend"
sudo -u "$APP_USER" npm ci || sudo -u "$APP_USER" npm install
sudo -u "$APP_USER" npm run build

echo "==> Setting up WhatsApp bridge"
cd "$APP_DIR/whatsapp_bridge"
sudo -u "$APP_USER" npm ci || sudo -u "$APP_USER" npm install
sudo -u "$APP_USER" cp ../deploy/non-docker/whatsapp.env.example .env
sudo -u "$APP_USER" sed -i \
  -e "s|^NEXUS_WEBHOOK_SECRET=.*|NEXUS_WEBHOOK_SECRET=${WHATSAPP_WEBHOOK_SECRET}|" \
  .env
sudo chmod 600 .env
sudo chown "$APP_USER:$APP_USER" .env

echo "==> Installing systemd services"
sudo cp "$APP_DIR/deploy/non-docker/nexus-api.service" /etc/systemd/system/nexus-api.service
sudo cp "$APP_DIR/deploy/non-docker/nexus-whatsapp.service" /etc/systemd/system/nexus-whatsapp.service
sudo cp "$APP_DIR/deploy/non-docker/nexus-vox-server.service" /etc/systemd/system/nexus-vox-server.service
sudo cp "$APP_DIR/deploy/non-docker/nexus-vox-worker.service" /etc/systemd/system/nexus-vox-worker.service
sudo systemctl daemon-reload
sudo systemctl enable --now nexus-api
sudo systemctl enable --now nexus-whatsapp
sudo systemctl enable --now nexus-vox-server
sudo systemctl enable --now nexus-vox-worker

echo "==> Installing nginx config"
if [[ "$SKIP_CERTBOT" == "1" ]]; then
  sudo cp "$APP_DIR/deploy/non-docker/nginx-nexusagent-http.conf" /etc/nginx/sites-available/nexusagent
else
  sudo cp "$APP_DIR/deploy/non-docker/nginx-nexusagent.conf" /etc/nginx/sites-available/nexusagent
fi
sudo ln -sf /etc/nginx/sites-available/nexusagent /etc/nginx/sites-enabled/nexusagent
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx

echo "==> Getting HTTPS certificates"
if [[ "$SKIP_CERTBOT" == "1" ]]; then
  echo "Skipping certbot because SKIP_CERTBOT=1. Run again after DNS points to this server."
else
  sudo certbot --nginx --non-interactive --agree-tos \
    --email "$LETSENCRYPT_EMAIL" \
    -d "$ROOT_DOMAIN" \
    -d "www.$ROOT_DOMAIN" \
    -d "$PRODUCT_DOMAIN" \
    -d "$VOX_DOMAIN"
fi

sudo systemctl restart nexus-api nexus-whatsapp nexus-vox-server nexus-vox-worker nginx

cat <<EOF

Done.

Landing:  https://${ROOT_DOMAIN}
Product:  https://${PRODUCT_DOMAIN}
Vox:      https://${VOX_DOMAIN}

Generated secrets are in:
  ${APP_DIR}/.env
  ${APP_DIR}/whatsapp_bridge/.env

Copy this VOICE_CALLBACK_SECRET into NexusCaller:
  ${VOICE_CALLBACK_SECRET}

Watch services:
  sudo journalctl -u nexus-api -f
  sudo journalctl -u nexus-whatsapp -f
  sudo journalctl -u nexus-vox-server -f
  sudo journalctl -u nexus-vox-worker -f

EOF
