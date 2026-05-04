#!/usr/bin/env bash
# First-time Let's Encrypt setup for NexusAgent + Vox.
# Run ONCE on a fresh EC2 after DNS A-records are pointing to this server's IP.
#
# Usage:  ./deploy/init-letsencrypt.sh <base-domain> <email>
# Example: ./deploy/init-letsencrypt.sh nexusapp.com admin@example.com
set -euo pipefail

DOMAIN="${1:?usage: $0 <base-domain> <email>}"
EMAIL="${2:?usage: $0 <base-domain> <email>}"
APP_DOMAIN="app.${DOMAIN}"
VOX_DOMAIN="vox.${DOMAIN}"

CONF_DIR="./data/certbot/conf"
WWW_DIR="./data/certbot/www"

echo "================================================================"
echo " Let's Encrypt setup"
echo "   App domain : $APP_DOMAIN"
echo "   Vox domain : $VOX_DOMAIN"
echo "   Email      : $EMAIL"
echo "================================================================"
echo ""

# 1. Confirm DNS is resolving before we waste an ACME attempt
for d in "$APP_DOMAIN" "$VOX_DOMAIN"; do
  if ! host "$d" >/dev/null 2>&1; then
    echo "ERROR: $d does not resolve. Point your DNS A-record to this server's IP first."
    exit 1
  fi
  echo "✓ DNS OK: $d"
done
echo ""

# 2. Patch the yourdomain.com placeholder in nginx.conf
sed -i "s/yourdomain\.com/${DOMAIN}/g" ./deploy/nginx.conf
echo "✓ nginx.conf updated with $DOMAIN"

# 3. Create directories
mkdir -p "$CONF_DIR/live/$APP_DOMAIN" "$CONF_DIR/live/$VOX_DOMAIN" "$WWW_DIR"

# 4. Dummy self-signed certs so nginx can start before real certs exist
for d in "$APP_DOMAIN" "$VOX_DOMAIN"; do
  if [[ ! -f "$CONF_DIR/live/$d/fullchain.pem" ]]; then
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
      -keyout "$CONF_DIR/live/$d/privkey.pem" \
      -out    "$CONF_DIR/live/$d/fullchain.pem" \
      -subj   "/CN=localhost" 2>/dev/null
    echo "✓ Dummy cert created for $d"
  fi
done
echo ""

# 5. Start nginx + certbot so nginx can serve the ACME challenge
echo "→ Starting proxy and certbot..."
docker compose up -d proxy certbot
sleep 3  # give nginx a moment to be ready

# 6. Issue real certs (replaces the dummy ones)
for d in "$APP_DOMAIN" "$VOX_DOMAIN"; do
  echo "→ Requesting cert for $d..."
  docker compose run --rm certbot certonly \
    --webroot --webroot-path /var/www/certbot \
    --email "$EMAIL" --agree-tos --no-eff-email \
    --force-renewal \
    -d "$d"
  echo "✓ Real cert issued for $d"
done
echo ""

# 7. Reload nginx to pick up the real certs
docker compose exec proxy nginx -s reload
echo "✓ nginx reloaded with real certs"
echo ""
echo "================================================================"
echo " HTTPS is live!"
echo "   https://$APP_DOMAIN"
echo "   https://$VOX_DOMAIN"
echo ""
echo " Next: docker compose up -d (starts the full stack)"
echo "================================================================"
