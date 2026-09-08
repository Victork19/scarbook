# Cloudflare Pages and API

## Pages project

Create a Cloudflare Pages project connected to this repository with:

```text
Root directory: apps/web
Build command: npm run build
Build output directory: dist
Environment variable: VITE_API_URL=https://api.YOURDOMAIN
```

`VITE_API_URL` is the only frontend runtime configuration. Never add `RYO_MCP_KEY` or any other backend secret to Pages variables.

## API DNS

Create an `api` DNS record pointing to the EC2 public IP. Proxy it through Cloudflare after the EC2 origin has a valid certificate. Use SSL/TLS mode **Full (strict)**.

The EC2 bootstrap is:

```bash
cd /opt/scarbook
sudo API_DOMAIN=api.example.com CERTBOT_EMAIL=ops@example.com bash ./deploy/install-ec2.sh
```

The bootstrap installs Docker, Compose, Nginx, and Certbot, provisions the systemd service, and starts the API. Put the real `RYO_MCP_KEY` in `/opt/scarbook/.env` before rerunning it.

For later releases:

```bash
cd /opt/scarbook
git pull --ff-only
sudo bash ./deploy/deploy-ec2.sh
```

The SQLite database and raw receipts live in the named Docker volume `scarbook-data`; rebuilding the image does not delete them.

## Caching

Add a Cloudflare cache rule to bypass `/api/*` and `/health`, and preserve `Cache-Control: no-store`. In particular, T1 must never be served from a cache.
