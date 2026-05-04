#!/usr/bin/env bash
# EC2 one-shot bootstrap for NexusAgent + nexuscaller-lab.
# Run as the ubuntu user on a fresh Ubuntu 22.04 t2.micro (AWS free tier) or larger.
# Security Group must have ports 22, 80, 443 open.
# Uses nip.io for free automatic HTTPS — no domain purchase needed.
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
  newgrp docker
  echo "✓ Docker installed"
else
  echo "✓ Docker already installed ($(docker --version))"
fi

# ── 2. Clone repos ───────────────────────────────────────────────────────────
cd "$HOME_DIR"

if [[ ! -d NexusAgent ]]; then
  git clone https://github.com/praneethhh18/NexusAgent.git
  echo "✓ NexusAgent cloned"
else
  git -C NexusAgent pull --ff-only
  echo "✓ NexusAgent up to date"
fi

if [[ ! -d nexuscaller-lab ]]; then
  git clone https://github.com/praneethhh18/NexusCaller-lab.git nexuscaller-lab
  echo "✓ nexuscaller-lab cloned"
else
  git -C nexuscaller-lab pull --ff-only
  echo "✓ nexuscaller-lab up to date"
fi
echo ""

# ── 3. Detect IP + set up domains ───────────────────────────────────────────
echo "→ Detecting public IP..."
PUBLIC_IP="$(curl -fsSL ifconfig.me)"
echo "✓ Public IP: $PUBLIC_IP"
echo ""
echo "  Domain options:"
echo "   1) I have a domain (e.g. nexusagent.in from BigRock)"
echo "   2) Use free nip.io  →  app.$PUBLIC_IP.nip.io  (IP-based, no purchase)"
echo ""
read -rp "→ Enter your base domain, or press Enter to use nip.io: " BASE_DOMAIN

if [[ -z "$BASE_DOMAIN" ]]; then
  APP_DOMAIN="app.${PUBLIC_IP}.nip.io"
  VOX_DOMAIN="vox.${PUBLIC_IP}.nip.io"
  ROOT_DOMAIN=""
  echo ""
  echo "  Using nip.io (no landing page domain — nip.io is subdomain-only):"
  echo "   App → https://$APP_DOMAIN"
  echo "   Vox → https://$VOX_DOMAIN"
else
  APP_DOMAIN="app.${BASE_DOMAIN}"
  VOX_DOMAIN="vox.${BASE_DOMAIN}"
  ROOT_DOMAIN="${BASE_DOMAIN}"
  echo ""
  echo "  Make sure these DNS A-records point to $PUBLIC_IP before continuing:"
  echo "   $BASE_DOMAIN        →  $PUBLIC_IP"
  echo "   www.$BASE_DOMAIN    →  $PUBLIC_IP"
  echo "   $APP_DOMAIN  →  $PUBLIC_IP"
  echo "   $VOX_DOMAIN  →  $PUBLIC_IP"
  echo ""
  read -rp "→ DNS records set? Press Enter to continue..."
fi
echo ""

read -rp "→ Email for Let's Encrypt SSL notices: " EMAIL

# ── 4. .env files ─────────────────────────────────────────────────────────────
NEXUS_ENV="$HOME_DIR/NexusAgent/.env"
VOX_ENV="$HOME_DIR/nexuscaller-lab/.env"

[[ -f "$NEXUS_ENV" ]] || cp "$HOME_DIR/NexusAgent/.env.example" "$NEXUS_ENV"
[[ -f "$VOX_ENV" ]]   || cp "$HOME_DIR/nexuscaller-lab/.env.example" "$VOX_ENV"

# Auto-inject all production values
CALLBACK_SECRET="$(openssl rand -hex 32)"

for ENV_FILE in "$NEXUS_ENV" "$VOX_ENV"; do
  sed -i "s|VOICE_CALLBACK_SECRET=.*|VOICE_CALLBACK_SECRET=${CALLBACK_SECRET}|" "$ENV_FILE"
done

sed -i "s|NEXUS_PUBLIC_URL=.*|NEXUS_PUBLIC_URL=https://${APP_DOMAIN}|"   "$NEXUS_ENV"
sed -i "s|VOX_PUBLIC_URL=.*|VOX_PUBLIC_URL=https://${VOX_DOMAIN}|"       "$NEXUS_ENV"
sed -i "s|APP_BASE_URL=.*|APP_BASE_URL=https://${APP_DOMAIN}|"           "$NEXUS_ENV"
sed -i "s|GOOGLE_OAUTH_REDIRECT_URI=.*|GOOGLE_OAUTH_REDIRECT_URI=https://${APP_DOMAIN}/api/calendar/oauth/callback|" "$NEXUS_ENV"

# Inject landing page URL if using a real domain
if [[ -n "$ROOT_DOMAIN" ]]; then
  sed -i "s|LANDING_URL=.*|LANDING_URL=https://${ROOT_DOMAIN}|" "$NEXUS_ENV" 2>/dev/null || true
fi

echo "✓ URLs + VOICE_CALLBACK_SECRET auto-injected"
echo ""

# ── 5. Prompt for API secrets ─────────────────────────────────────────────────
echo "┌─────────────────────────────────────────────────────────────┐"
echo "│  Now fill in your API keys in both .env files:             │"
echo "│                                                             │"
echo "│  nano $NEXUS_ENV"
echo "│    → ANTHROPIC_API_KEY   (console.anthropic.com)           │"
echo "│    → JWT_SECRET          (any random string)               │"
echo "│                                                             │"
echo "│  nano $VOX_ENV"
echo "│    → LIVEKIT_URL         (your LiveKit Cloud project URL)  │"
echo "│    → LIVEKIT_API_KEY                                       │"
echo "│    → LIVEKIT_API_SECRET                                    │"
echo "│    → LIVEKIT_OUTBOUND_TRUNK_ID  (Twilio SIP trunk)         │"
echo "│    → GROQ_API_KEY        (console.groq.com — free)         │"
echo "│    → ELEVENLABS_API_KEY  (elevenlabs.io — free tier)       │"
echo "└─────────────────────────────────────────────────────────────┘"
echo ""
read -rp "→ Done filling in both .env files? [y/N]: " CONFIRM
[[ "$CONFIRM" =~ ^[Yy]$ ]] || { echo "Re-run this script once done."; exit 0; }

# ── 6. Pull images from GHCR ─────────────────────────────────────────────────
echo ""
echo "→ Pulling Docker images from GHCR..."
cd "$HOME_DIR/NexusAgent"
docker compose pull

# ── 7. SSL certificates (Let's Encrypt via nip.io) ───────────────────────────
echo ""
echo "→ Getting free SSL certificates..."
chmod +x ./deploy/init-letsencrypt.sh
./deploy/init-letsencrypt.sh "$APP_DOMAIN" "$VOX_DOMAIN" "$EMAIL" "${ROOT_DOMAIN:-}"

# ── 8. Start full stack ───────────────────────────────────────────────────────
echo ""
echo "→ Starting full stack..."
docker compose up -d

echo ""
echo "========================================================"
echo " All done! Your NexusAgent is live:"
echo ""
[[ -n "${ROOT_DOMAIN:-}" ]] && echo "   Landing → https://$ROOT_DOMAIN"
echo "   App     → https://$APP_DOMAIN"
echo "   Vox     → https://$VOX_DOMAIN"
echo ""
echo " Add these to GitHub Actions secrets (both repos):"
echo "   EC2_HOST   = $PUBLIC_IP"
echo "   EC2_SSH_KEY = (paste your .pem private key contents)"
echo "========================================================"
