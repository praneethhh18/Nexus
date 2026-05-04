#!/usr/bin/env bash
# EC2 one-shot bootstrap for NexusAgent + nexuscaller-lab.
# Run as the ubuntu user on a fresh Ubuntu 22.04 t3.medium.
# Security Group must have ports 22, 80, 443 open.
#
# Usage:
#   curl -fsSL https://raw.githubusercontent.com/praneethhh18/NexusAgent/main/deploy/ec2-bootstrap.sh | bash
set -euo pipefail

HOME_DIR="/home/ubuntu"

echo "========================================================"
echo " NexusAgent EC2 Bootstrap"
echo " $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "========================================================"
echo ""

# ── 1. Docker ────────────────────────────────────────────────────────────────
if ! command -v docker &>/dev/null; then
  echo "→ Installing Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker ubuntu
  echo "✓ Docker installed"
  echo "  NOTE: log out and back in (or run 'newgrp docker') for the group to apply."
  echo "  Re-run this script after re-login if needed."
else
  echo "✓ Docker already installed ($(docker --version))"
fi

# ── 2. Clone repos ───────────────────────────────────────────────────────────
cd "$HOME_DIR"

if [[ ! -d NexusAgent ]]; then
  git clone https://github.com/praneethhh18/NexusAgent.git
  echo "✓ NexusAgent cloned"
else
  echo "✓ NexusAgent already present — pulling latest..."
  git -C NexusAgent pull --ff-only
fi

if [[ ! -d nexuscaller-lab ]]; then
  git clone https://github.com/praneethhh18/nexuscaller-lab.git
  echo "✓ nexuscaller-lab cloned"
else
  echo "✓ nexuscaller-lab already present — pulling latest..."
  git -C nexuscaller-lab pull --ff-only
fi
echo ""

# ── 3. Domain — ask early so we can pre-fill env files ──────────────────────
PUBLIC_IP="$(curl -fsSL ifconfig.me 2>/dev/null || echo '<unknown>')"
echo "  This server's public IP: $PUBLIC_IP"
echo "  Make sure DNS A-records for app.<domain> and vox.<domain> point here."
echo ""
read -rp "→ Base domain (e.g. nexusapp.com): " DOMAIN
read -rp "→ Email for Let's Encrypt notices: " EMAIL
APP_DOMAIN="app.${DOMAIN}"
VOX_DOMAIN="vox.${DOMAIN}"

# ── 4. .env files ─────────────────────────────────────────────────────────────
NEXUS_ENV="$HOME_DIR/NexusAgent/.env"
VOX_ENV="$HOME_DIR/nexuscaller-lab/.env"

if [[ ! -f "$NEXUS_ENV" ]]; then
  cp "$HOME_DIR/NexusAgent/.env.example" "$NEXUS_ENV"
fi
if [[ ! -f "$VOX_ENV" ]]; then
  cp "$HOME_DIR/nexuscaller-lab/.env.example" "$VOX_ENV"
fi

# Auto-inject production URLs and a shared callback secret
CALLBACK_SECRET="$(openssl rand -hex 32)"
for ENV_FILE in "$NEXUS_ENV" "$VOX_ENV"; do
  sed -i "s|VOICE_CALLBACK_SECRET=.*|VOICE_CALLBACK_SECRET=${CALLBACK_SECRET}|" "$ENV_FILE"
done
sed -i "s|NEXUS_PUBLIC_URL=.*|NEXUS_PUBLIC_URL=https://${APP_DOMAIN}|" "$NEXUS_ENV"
sed -i "s|VOX_PUBLIC_URL=.*|VOX_PUBLIC_URL=https://${VOX_DOMAIN}|"     "$NEXUS_ENV"
sed -i "s|APP_BASE_URL=.*|APP_BASE_URL=https://${APP_DOMAIN}|"         "$NEXUS_ENV"
sed -i "s|GOOGLE_OAUTH_REDIRECT_URI=.*|GOOGLE_OAUTH_REDIRECT_URI=https://${APP_DOMAIN}/api/calendar/oauth/callback|" "$NEXUS_ENV"
echo "✓ Production URLs + shared VOICE_CALLBACK_SECRET injected into both .env files"
echo ""

echo "┌────────────────────────────────────────────────────────────┐"
echo "│ Fill in API secrets before continuing:                     │"
echo "│                                                            │"
echo "│  nano $NEXUS_ENV"
echo "│  Required: ANTHROPIC_API_KEY (or AWS Bedrock creds)       │"
echo "│            JWT_SECRET (pick any random string)            │"
echo "│                                                            │"
echo "│  nano $VOX_ENV"
echo "│  Required: LIVEKIT_URL, LIVEKIT_API_KEY,                  │"
echo "│            LIVEKIT_API_SECRET, LIVEKIT_OUTBOUND_TRUNK_ID  │"
echo "│            GROQ_API_KEY, ELEVENLABS_API_KEY               │"
echo "└────────────────────────────────────────────────────────────┘"
echo ""
read -rp "→ Have you filled in both .env files? [y/N]: " CONFIRM
if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
  echo "Fill them in, then re-run from step 4 (images are already pulled)."
  exit 0
fi

# ── 5. Pull images from GHCR ──────────────────────────────────────────────────
echo ""
echo "→ Pulling images from GHCR..."
cd "$HOME_DIR/NexusAgent"
docker compose pull

# ── 6. SSL certificates ───────────────────────────────────────────────────────
echo ""
chmod +x ./deploy/init-letsencrypt.sh
./deploy/init-letsencrypt.sh "$DOMAIN" "$EMAIL"

# ── 7. Start full stack ───────────────────────────────────────────────────────
echo ""
echo "→ Starting full stack..."
docker compose up -d

echo ""
echo "========================================================"
echo " Bootstrap complete!"
echo ""
echo "   App  → https://${APP_DOMAIN}"
echo "   Vox  → https://${VOX_DOMAIN}"
echo ""
echo " Optional services:"
echo "   docker compose --profile backup up -d   # nightly DB backup"
echo "   docker compose --profile bridge up -d   # WhatsApp bridge"
echo ""
echo " Add these secrets to GitHub Actions (Settings → Secrets):"
echo "   In NexusAgent repo:       EC2_HOST=${PUBLIC_IP}"
echo "   In nexuscaller-lab repo:  EC2_HOST=${PUBLIC_IP}"
echo "   In both repos:            EC2_SSH_KEY=(your private key contents)"
echo "========================================================"
