#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/scarbook}"
API_DOMAIN="${API_DOMAIN:-api.YOURDOMAIN}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"

if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -E env APP_DIR="$APP_DIR" API_DOMAIN="$API_DOMAIN" CERTBOT_EMAIL="$CERTBOT_EMAIL" "$0" "$@"
fi

if [[ ! -f "$APP_DIR/docker-compose.yml" ]]; then
  echo "Expected the repository at $APP_DIR" >&2
  exit 1
fi

export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y ca-certificates curl nginx certbot python3-certbot-nginx

if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sh
fi
if ! docker compose version >/dev/null 2>&1; then
  apt-get install -y docker-compose-plugin || apt-get install -y docker-compose-v2
fi
docker compose version >/dev/null 2>&1 || { echo "Docker Compose v2 is required." >&2; exit 1; }
systemctl enable --now docker nginx

install -d -m 0700 /var/lib/scarbook
install -d -m 0755 /var/www/html

if [[ ! -f "$APP_DIR/.env" ]]; then
  cp "$APP_DIR/.env.example" "$APP_DIR/.env"
  chmod 600 "$APP_DIR/.env"
  echo "Created $APP_DIR/.env. Add RYO_MCP_KEY and production CORS_ORIGINS, then rerun this script." >&2
  exit 1
fi

if [[ "$API_DOMAIN" == "api.YOURDOMAIN" ]]; then
  echo "Set API_DOMAIN to the real API hostname before running this script." >&2
  exit 1
fi

sed "s/api\.YOURDOMAIN/$API_DOMAIN/g" "$APP_DIR/deploy/nginx-scarbook.conf" > /etc/nginx/sites-available/scarbook
ln -sfn /etc/nginx/sites-available/scarbook /etc/nginx/sites-enabled/scarbook
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

if [[ -n "$CERTBOT_EMAIL" ]]; then
  certbot --nginx --non-interactive --agree-tos --email "$CERTBOT_EMAIL" --redirect -d "$API_DOMAIN"
else
  echo "CERTBOT_EMAIL not set; HTTP is configured. Run certbot later for HTTPS." >&2
fi

install -m 0644 "$APP_DIR/deploy/scarbook.service" /etc/systemd/system/scarbook.service
systemctl daemon-reload
systemctl enable --now scarbook.service

echo "Scarbook API is running on 127.0.0.1:8000 behind Nginx at https://$API_DOMAIN"
