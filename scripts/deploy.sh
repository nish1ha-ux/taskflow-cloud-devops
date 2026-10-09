#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Deploy TaskFlow Cloud & DevOps stack (idempotent)
# ------------------------------------------------------------

# Determine repository root (inner repo)
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# 1. Pull latest code (optional if already up‑to‑date)
git fetch --all
git checkout main
git pull origin main

# Stop host-level nginx if active so containerized Nginx can bind port 80/443
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl stop nginx 2>/dev/null || true
  sudo systemctl disable nginx 2>/dev/null || true
fi

# 2. Build or pull images
docker compose build app

# 3. Bring up the stack (keep existing volumes, do not delete data)
docker compose up -d --remove-orphans

# 4. Wait for the HTTP health endpoint (max 30 s)
echo "⏳ Waiting for HTTP health check …"
for i in {1..30}; do
  if curl -fs -H "Host: 13-233-154-188.nip.io" http://127.0.0.1/health >/dev/null 2>&1 || curl -fs http://127.0.0.1/health >/dev/null 2>&1; then
    echo "✅ HTTP health check passed"
    break
  fi
  sleep 1
done

if ! curl -fs -H "Host: 13-233-154-188.nip.io" http://127.0.0.1/health >/dev/null 2>&1 && ! curl -fs http://127.0.0.1/health >/dev/null 2>&1; then
  echo "❌ HTTP health check failed after timeout"
  exit 1
fi

# 5. Certificate handling – do **not** run Certbot automatically.
# If the certificate already exists, switch Nginx to HTTPS configuration.
CERT_PATH="/etc/letsencrypt/live/13-233-154-188.nip.io/fullchain.pem"
if docker compose exec nginx test -f "$CERT_PATH"; then
  echo "🔐 Certificate already present – switching Nginx to HTTPS"
  # Use the env var to select the HTTPS config and reload Nginx
  docker compose down nginx
  NGINX_CONF=https.conf docker compose up -d nginx
  # Verify HTTPS health
  echo "⏳ Verifying HTTPS health …"
  if curl -kfs https://13-233-154-188.nip.io/health >/dev/null; then
    echo "✅ HTTPS health check passed"
    exit 0
  else
    echo "⚠️ HTTPS health check failed – inspect logs"
    exit 1
  fi
else
  echo "🔔 Certificate not found. After the HTTP health check passes, run the following manually to obtain the certificate:"
  echo "    docker compose run --rm certbot"
  echo "Then re‑run this script to switch to HTTPS."
fi
