#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR="${APP_DIR:-/opt/scarbook}"
if [[ "${EUID}" -ne 0 ]]; then
  exec sudo -E env APP_DIR="$APP_DIR" "$0" "$@"
fi

cd "$APP_DIR"
test -f .env || { echo "Missing $APP_DIR/.env" >&2; exit 1; }
docker compose --env-file .env config >/dev/null
docker compose --env-file .env up -d --build --remove-orphans
docker image prune -f >/dev/null

attempt=0
while (( attempt < 20 )); do
  if curl --fail --silent http://127.0.0.1:8000/health >/dev/null; then
    echo "Scarbook API is healthy."
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 2
done

docker compose --env-file .env ps
echo "Scarbook API did not become healthy." >&2
exit 1
