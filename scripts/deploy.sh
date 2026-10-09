#!/usr/bin/env bash
set -euo pipefail

# ------------------------------------------------------------
# Deploy TaskFlow Cloud & DevOps stack (idempotent)
# ------------------------------------------------------------

# Determine repository root (inner repo)
REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

# Safe directory configuration
git config --global --add safe.directory "$REPO_ROOT" 2>/dev/null || true

# 1. Pull latest code (optional if already up-to-date)
git fetch origin main || true
git checkout main || true
git reset --hard origin/main || git pull origin main || true

# Stop host-level nginx if active so containerized Nginx can bind port 80/443
if command -v systemctl >/dev/null 2>&1; then
  sudo systemctl stop nginx 2>/dev/null || true
  sudo systemctl disable nginx 2>/dev/null || true
fi

# 2. Build or pull images
if [ -n "${APP_IMAGE:-}" ]; then
  echo "📥 Pulling image $APP_IMAGE..."
  docker pull "$APP_IMAGE" || docker compose build app
else
  docker compose pull app 2>/dev/null || docker compose build app
fi

# 3. Check if SSL certificate is already present in docker volume
CERT_EXISTS=false
if docker compose run --rm --no-deps --entrypoint "test -f /etc/letsencrypt/live/13-233-154-188.nip.io/fullchain.pem" certbot >/dev/null 2>&1; then
  CERT_EXISTS=true
fi

if [ "$CERT_EXISTS" = true ]; then
  echo "🔐 SSL certificate detected. Starting stack in HTTPS mode..."
  NGINX_CONF=https.conf docker compose up -d --force-recreate --remove-orphans
else
  echo "🌐 Starting stack in HTTP mode for initial setup / challenge..."
  NGINX_CONF=http.conf docker compose up -d --force-recreate --remove-orphans
fi

# 4. Wait for health check (follow redirects with -L for HTTPS)
echo "⏳ Waiting for application health check …"
HEALTHY=false
for i in {1..30}; do
  if curl -kfsL -H "Host: 13-233-154-188.nip.io" http://127.0.0.1/health >/dev/null 2>&1 || curl -kfsL http://127.0.0.1/health >/dev/null 2>&1; then
    echo "✅ Health check passed"
    HEALTHY=true
    break
  fi
  sleep 1
done

if [ "$HEALTHY" != true ]; then
  echo "❌ Health check failed after timeout"
  exit 1
fi

# 5. Certificate handling
if [ "$CERT_EXISTS" = true ]; then
  # Verify HTTPS health specifically
  echo "⏳ Verifying HTTPS endpoint health …"
  if curl -kfsL https://13-233-154-188.nip.io/health >/dev/null 2>&1; then
    echo "✅ HTTPS health check passed successfully"
    exit 0
  else
    echo "⚠️ HTTPS health check failed – inspect logs"
    exit 1
  fi
else
  echo "🔔 SSL certificate not found. Run the following to obtain the certificate:"
  echo "    docker compose run --rm certbot"
  echo "Then re-run this script to activate HTTPS."
fi
