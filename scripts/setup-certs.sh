#!/usr/bin/env bash
# ==============================================================================
# Nemo Platform — SSL/TLS Certificate Setup (Development)
# Uses mkcert to generate locally-trusted certificates
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
CERT_DIR="$PROJECT_ROOT/infra/certs"

DOMAINS=(
  "nemo.local"
  "api.nemo.local"
  "grafana.nemo.local"
  "prometheus.nemo.local"
  "traefik.nemo.local"
)

echo "=== Nemo TLS Certificate Setup ==="
echo ""

# Check for mkcert
if ! command -v mkcert &>/dev/null; then
  echo "❌ mkcert is not installed."
  echo ""
  echo "Install it:"
  echo "  Ubuntu/Debian: sudo apt install mkcert"
  echo "  macOS:         brew install mkcert"
  echo "  Arch:          sudo pacman -S mkcert"
  echo ""
  echo "Then run: mkcert -install"
  exit 1
fi

# Install the local CA (if not already done)
echo "→ Installing local CA (mkcert -install)..."
mkcert -install

# Generate certificates
echo "→ Generating certificates for: ${DOMAINS[*]}"
mkdir -p "$CERT_DIR"

mkcert \
  -cert-file "$CERT_DIR/nemo.local+4.pem" \
  -key-file "$CERT_DIR/nemo.local+4-key.pem" \
  "${DOMAINS[@]}"

echo ""
echo "✅ Certificates generated:"
echo "   Cert: $CERT_DIR/nemo.local+4.pem"
echo "   Key:  $CERT_DIR/nemo.local+4-key.pem"
echo ""
echo "Domains covered:"
for d in "${DOMAINS[@]}"; do
  echo "   - $d"
done
