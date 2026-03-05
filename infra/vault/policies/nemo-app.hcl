# ==============================================================================
# HashiCorp Vault — Policy for Nemo Application Services
# ==============================================================================

# Read-only access to all nemo secrets
path "secret/data/nemo/*" {
  capabilities = ["read", "list"]
}

# Allow token renewal
path "auth/token/renew-self" {
  capabilities = ["update"]
}

# Allow token lookup
path "auth/token/lookup-self" {
  capabilities = ["read"]
}
