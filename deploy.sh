#!/usr/bin/env bash
set -euo pipefail

# Delegate to the comprehensive deployment script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
chmod +x "${SCRIPT_DIR}/scripts/deploy.sh" 2>/dev/null || true
exec bash "${SCRIPT_DIR}/scripts/deploy.sh" "$@"
