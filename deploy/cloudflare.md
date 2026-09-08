# Cloudflare Pages and API

## Pages project

Create a Cloudflare Pages project connected to this repository with:

```text
Root directory: apps/web
Build command: npm run build
Build output directory: dist
Environment variable: VITE_API_URL=https://scarbook.duckdns.org
```

`VITE_API_URL` is the only frontend runtime configuration. Never add `RYO_MCP_KEY` or any other backend secret to Pages variables.

## API DNS and Docker HTTPS

Point `scarbook.duckdns.org` at the EC2 public IP and allow inbound TCP ports 80 and 443 in the EC2 Security Group. The Docker Compose stack includes Caddy, which terminates HTTPS and automatically obtains and renews the certificate.

Configure the backend:

```bash
cd /opt/scarbook
cp .env.example .env
# Set PUBLIC_DOMAIN=scarbook.duckdns.org, RYO_MCP_KEY, and LLM_API_KEY.
sudo docker compose --env-file .env up -d --build
```

For later releases:

```bash
cd /opt/scarbook
git pull --ff-only
sudo docker compose --env-file .env up -d --build --remove-orphans
```

The SQLite database and raw receipts live in the named Docker volume `scarbook-data`; rebuilding the image does not delete them.

## Caching

Add a Cloudflare cache rule to bypass `/api/*` and `/health`, and preserve `Cache-Control: no-store`. In particular, T1 must never be served from a cache.
