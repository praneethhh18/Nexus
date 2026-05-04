#!/usr/bin/env bash
# First-time Let's Encrypt setup for NexusAgent + Vox.
# Run ONCE on a fresh EC2 after the Elastic IP is attached.
#
# Usage:  ./deploy/init-letsencrypt.sh <app-domain> <vox-domain> <email>
# Example (nip.io):  ./deploy/init-letsencrypt.sh app.54.123.45.67.nip.io vox.54.123.45.67.nip.io admin@gmail.com
# Example (custom):  ./deploy/init-letsencrypt.sh app.mycompany.com vox.mycompany.com admin@mycompany.com
set -euo pipefail

APP_DOMAIN="${1:?usage: $0 <app-domain> <vox-domain> <email>}"
VOX_DOMAIN="${2:?usage: $0 <app-domain> <vox-domain> <email>}"
EMAIL="${3:?usage: $0 <app-domain> <vox-domain> <email>}"

CONF_DIR="./data/certbot/conf"
WWW_DIR="./data/certbot/www"

echo "================================================================"
echo " Let's Encrypt setup"
echo "   App : $APP_DOMAIN"
echo "   Vox : $VOX_DOMAIN"
echo "   Email: $EMAIL"
echo "================================================================"
echo ""

# 1. Confirm DNS resolves before wasting an ACME attempt
for d in "$APP_DOMAIN" "$VOX_DOMAIN"; do
  if ! host "$d" >/dev/null 2>&1; then
    echo "ERROR: $d does not resolve. Check your IP / nip.io domain and try again."
    exit 1
  fi
  echo "✓ DNS OK: $d"
done
echo ""

# 2. Patch domain placeholders in nginx.conf
sed -i "s|app\.yourdomain\.com|${APP_DOMAIN}|g" ./deploy/nginx.conf
sed -i "s|vox\.yourdomain\.com|${VOX_DOMAIN}|g" ./deploy/nginx.conf
echo "✓ nginx.conf updated"

# 3. Create cert directories
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

# 5. Start nginx + certbot (nginx serves the ACME challenge on port 80)
echo "→ Starting proxy and certbot..."
docker compose up -d proxy certbot
sleep 3

# 6. Issue real certs
for d in "$APP_DOMAIN" "$VOX_DOMAIN"; do
  echo "→ Requesting cert for $d..."
  docker compose run --rm certbot certonly \
    --webroot --webroot-path /var/www/certbot \
    --email "$EMAIL" --agree-tos --no-eff-email \
    --force-renewal \
    -d "$d"
  echo "✓ Cert issued for $d"
done
echo ""

# 7. Reload nginx with real certs
docker compose exec proxy nginx -s reload
echo "✓ nginx reloaded"
echo ""
echo "================================================================"
echo " HTTPS is live!"
echo "   https://$APP_DOMAIN"
echo "   https://$VOX_DOMAIN"
echo "================================================================"
