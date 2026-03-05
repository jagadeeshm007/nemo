#!/usr/bin/env bash
# ==============================================================================
# Nemo Platform — Development Environment Setup
# Sets up /etc/hosts, SSL certs, env files, and starts services
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "============================================"
echo "   Nemo Platform — Dev Environment Setup"
echo "============================================"
echo ""

# ----------------------------------------------------------
# 1. /etc/hosts entries
# ----------------------------------------------------------
DOMAINS=(
  "nemo.local"
  "api.nemo.local"
  "grafana.nemo.local"
  "prometheus.nemo.local"
  "traefik.nemo.local"
)

echo "=== Step 1: Local Domain Setup ==="
HOSTS_MODIFIED=false
for domain in "${DOMAINS[@]}"; do
  if ! grep -q "$domain" /etc/hosts 2>/dev/null; then
    echo "  Adding $domain to /etc/hosts (requires sudo)..."
    echo "127.0.0.1 $domain" | sudo tee -a /etc/hosts >/dev/null
    HOSTS_MODIFIED=true
  else
    echo "  ✓ $domain already in /etc/hosts"
  fi
done

if $HOSTS_MODIFIED; then
  echo "  ✅ /etc/hosts updated"
else
  echo "  ✅ All domains already configured"
fi
echo ""

# ----------------------------------------------------------
# 2. SSL certificates
# ----------------------------------------------------------
echo "=== Step 2: SSL Certificates ==="
CERT_DIR="$PROJECT_ROOT/infra/certs"
if [[ -f "$CERT_DIR/nemo.local+4.pem" && -f "$CERT_DIR/nemo.local+4-key.pem" ]]; then
  echo "  ✅ Certificates already exist"
else
  echo "  Generating certificates..."
  bash "$SCRIPT_DIR/setup-certs.sh"
fi
echo ""

# ----------------------------------------------------------
# 3. Environment files
# ----------------------------------------------------------
echo "=== Step 3: Environment Files ==="
if [[ ! -f "$PROJECT_ROOT/.env" ]]; then
  echo "  Creating .env from .env.dev..."
  cp "$PROJECT_ROOT/.env.dev" "$PROJECT_ROOT/.env"
  echo "  ✅ .env created (review and update API keys)"
else
  echo "  ✅ .env already exists"
fi
echo ""

# ----------------------------------------------------------
# 4. Docker network check
# ----------------------------------------------------------
echo "=== Step 4: Docker Networks ==="
for net in nemo-frontend nemo-backend nemo-infra; do
  if ! docker network ls --format '{{.Name}}' | grep -q "^${net}$"; then
    echo "  Creating network: $net"
    docker network create "$net" >/dev/null 2>&1 || true
  else
    echo "  ✓ $net already exists"
  fi
done
echo "  ✅ Networks ready"
echo ""

# ----------------------------------------------------------
# 5. Start services
# ----------------------------------------------------------
echo "=== Step 5: Starting Services ==="
echo "  Run one of:"
echo "    make dev-up          # Uses docker-compose.dev.yml"
echo "    make prod-up         # Uses docker-compose.prod.yml"
echo ""
echo "============================================"
echo "  Dev URLs (after starting services):"
echo "    Frontend:    https://nemo.local"
echo "    API:         https://api.nemo.local"
echo "    Grafana:     https://grafana.nemo.local"
echo "    Prometheus:  https://prometheus.nemo.local"
echo "    Traefik:     https://traefik.nemo.local"
echo "============================================"
