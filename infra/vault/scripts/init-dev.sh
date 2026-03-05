#!/bin/bash
# ==============================================================================
# Vault — Development Initialization Script
# ==============================================================================
# Initializes Vault with secrets for the Nemo platform (dev environment only).
# In production, use Vault auto-unseal with cloud KMS.
# ==============================================================================

set -euo pipefail

VAULT_ADDR="${VAULT_ADDR:-http://vault:8200}"
export VAULT_ADDR

echo "⏳ Waiting for Vault to be ready..."
until vault status 2>/dev/null | grep -q "Initialized.*true"; do
  # Check if vault needs initialization
  if vault status 2>&1 | grep -q "Initialized.*false"; then
    echo "🔑 Initializing Vault..."
    vault operator init -key-shares=1 -key-threshold=1 \
      -format=json > /vault/data/init.json

    UNSEAL_KEY=$(cat /vault/data/init.json | jq -r '.unseal_keys_b64[0]')
    ROOT_TOKEN=$(cat /vault/data/init.json | jq -r '.root_token')

    echo "🔓 Unsealing Vault..."
    vault operator unseal "$UNSEAL_KEY"

    export VAULT_TOKEN="$ROOT_TOKEN"
    break
  fi
  sleep 2
done

# If already initialized, unseal and login
if [ -f /vault/data/init.json ]; then
  UNSEAL_KEY=$(cat /vault/data/init.json | jq -r '.unseal_keys_b64[0]')
  ROOT_TOKEN=$(cat /vault/data/init.json | jq -r '.root_token')

  if vault status 2>&1 | grep -q "Sealed.*true"; then
    echo "🔓 Unsealing Vault..."
    vault operator unseal "$UNSEAL_KEY"
  fi

  export VAULT_TOKEN="$ROOT_TOKEN"
fi

echo "✅ Vault is ready"

# Enable KV v2 secrets engine
vault secrets enable -path=secret -version=2 kv 2>/dev/null || true

# Write application policy
vault policy write nemo-app /vault/policies/nemo-app.hcl

# Store Nemo platform secrets
echo "📝 Writing Nemo secrets..."

vault kv put secret/nemo/database \
  host=postgres \
  port=5432 \
  username="${POSTGRES_USER:-nemo}" \
  password="${POSTGRES_PASSWORD:-nemo_dev_secret_2024}" \
  database="${POSTGRES_DB:-nemo}"

vault kv put secret/nemo/redis \
  host=redis \
  port=6379 \
  password="${REDIS_PASSWORD:-redis_dev_secret_2024}"

vault kv put secret/nemo/kafka \
  brokers=kafka:29092 \
  group_id=nemo-platform

vault kv put secret/nemo/llm \
  openai_api_key="${OPENAI_API_KEY:-}" \
  anthropic_api_key="${ANTHROPIC_API_KEY:-}" \
  google_api_key="${GOOGLE_API_KEY:-}"

vault kv put secret/nemo/auth \
  jwt_secret="${GATEWAY_JWT_SECRET:-dev-jwt-secret-change-in-production-2024}" \
  keycloak_client_secret="${KEYCLOAK_CLIENT_SECRET:-nemo-client-secret}"

vault kv put secret/nemo/oauth \
  google_client_id="${GOOGLE_OAUTH_CLIENT_ID:-}" \
  google_client_secret="${GOOGLE_OAUTH_CLIENT_SECRET:-}" \
  github_client_id="${GITHUB_OAUTH_CLIENT_ID:-}" \
  github_client_secret="${GITHUB_OAUTH_CLIENT_SECRET:-}"

# Create an app role token for services
vault auth enable approle 2>/dev/null || true
vault write auth/approle/role/nemo-services \
  token_policies="nemo-app" \
  token_ttl=1h \
  token_max_ttl=4h

# Get role-id and secret-id for services
ROLE_ID=$(vault read -field=role_id auth/approle/role/nemo-services/role-id)
SECRET_ID=$(vault write -field=secret_id -f auth/approle/role/nemo-services/secret-id)

echo "📋 AppRole Credentials (for services):"
echo "   VAULT_ROLE_ID=$ROLE_ID"
echo "   VAULT_SECRET_ID=$SECRET_ID"

echo "✅ Vault initialization complete"
