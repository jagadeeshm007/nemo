# Nemo Platform — Networking & Security Architecture

## Overview

The Nemo platform uses **Traefik** as a reverse proxy with TLS termination, **Docker network isolation** for security segmentation, and separate **dev/prod environments** with appropriate configs.

## Architecture

```
                    Internet / localhost
                          │
                    ┌─────┴──────┐
                    │  Traefik   │  :80 (HTTP→HTTPS redirect)
                    │  (proxy)   │  :443 (HTTPS)
                    └──┬───┬───┬─┘  :9090 (gRPC)
                       │   │   │
          ┌────────────┘   │   └────────────┐
          │                │                │
   ┌──────┴──────┐ ┌──────┴──────┐ ┌───────┴───────┐
   │  Frontend   │ │ API Gateway │ │  Observability │
   │ nemo.local  │ │api.nemo.local│ │grafana/prom   │
   └─────────────┘ └──────┬──────┘ └───────────────┘
                          │
              ┌───────────┼───────────┐
              │           │           │
        ┌─────┴──┐  ┌────┴────┐ ┌────┴────┐
        │   AI   │  │ Plugin  │ │Workflow │  (backend-network)
        │Service │  │ Service │ │ Service │
        └───┬────┘  └────┬────┘ └────┬────┘
            │             │           │
       ┌────┴─────────────┴───────────┴────┐
       │     Postgres / Redis / Kafka /    │  (infra-network)
       │     ChromaDB / Loki / Promtail    │
       └───────────────────────────────────┘
```

## Networks

| Network         | Type              | Purpose                          | Services                                                                              |
| --------------- | ----------------- | -------------------------------- | ------------------------------------------------------------------------------------- |
| `nemo-frontend` | bridge            | Public-facing traffic            | traefik, frontend, api-gateway                                                        |
| `nemo-backend`  | bridge (internal) | Service-to-service communication | api-gateway, ai-service, plugin-service, workflow-service, vector-service, prometheus |
| `nemo-infra`    | bridge (internal) | Database/infrastructure access   | All backend + infra services, traefik                                                 |

> `internal: true` means no direct internet access — traffic must go through Traefik.

## Domains (Development)

| Domain                          | Service              | Port     |
| ------------------------------- | -------------------- | -------- |
| `https://nemo.local`            | Frontend (Next.js)   | 3000     |
| `https://api.nemo.local`        | API Gateway (Go/Gin) | 8080     |
| `https://grafana.nemo.local`    | Grafana              | 3000     |
| `https://prometheus.nemo.local` | Prometheus           | 9090     |
| `https://traefik.nemo.local`    | Traefik Dashboard    | internal |

## Quick Start

### 1. First-time setup

```bash
make setup    # configures /etc/hosts, generates SSL certs, creates .env
```

### 2. Start development

```bash
make dev-up   # starts all services with dev overrides
```

### 3. Start production

```bash
make prod-up  # starts all services with prod overrides
```

## SSL/TLS

### Development

- Uses **mkcert** to generate locally-trusted certificates
- Certificates stored in `infra/certs/` (gitignored)
- Run `scripts/setup-certs.sh` or `make setup` to generate

### Production

- Uses **Let's Encrypt** via Traefik's ACME resolver
- Set `ACME_EMAIL` in `.env.prod`
- Certificates auto-renewed and stored in Docker volume `traefik_acme`

## Environment Configuration

| File           | Purpose                                               |
| -------------- | ----------------------------------------------------- |
| `.env.example` | Template — copy and customize                         |
| `.env.dev`     | Development defaults (committed)                      |
| `.env.prod`    | Production template — update with real secrets        |
| `.env`         | Active config (gitignored) — used by `docker compose` |

### Secrets Management

- **Never commit** `.env` with real API keys or passwords
- Production: Use Docker Secrets or a vault (HashiCorp Vault, AWS Secrets Manager)
- Development: `.env.dev` has safe defaults for local use

## Docker Compose Files

| File                      | Purpose                                                            |
| ------------------------- | ------------------------------------------------------------------ |
| `docker-compose.base.yml` | Base service definitions, networks, volumes                        |
| `docker-compose.dev.yml`  | Dev overrides: debug ports, mkcert TLS, verbose logging            |
| `docker-compose.prod.yml` | Prod overrides: Let's Encrypt TLS, resource limits, no debug ports |
| `docker-compose.yml`      | Legacy single-file (kept for backward compatibility)               |

### Usage

```bash
# Development (equivalent to make dev-up)
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml --env-file .env.dev up --build -d

# Production (equivalent to make prod-up)
docker compose -f docker-compose.base.yml -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

## Production Hardening

### Traefik Middlewares (defined in `infra/proxy/dynamic/middlewares.yml`)

| Middleware          | Purpose                                                |
| ------------------- | ------------------------------------------------------ |
| `redirect-to-https` | Forces HTTP → HTTPS redirect                           |
| `secure-headers`    | XSS filter, HSTS, nosniff, frame deny, referrer policy |
| `rate-limit`        | General: 100 req/s avg, 200 burst                      |
| `api-rate-limit`    | API: 50 req/s avg, 100 burst                           |
| `request-size`      | Max 10MB request body                                  |
| `cors-headers`      | CORS for frontend origins                              |
| `gzip-compress`     | Response compression                                   |
| `retry-middleware`  | 3 retries with 100ms backoff                           |
| `circuit-breaker`   | Opens on >30% network errors or >25% 5xx               |
| `admin-auth`        | Basic auth for observability tools (prod)              |

### TLS Configuration

- **Dev**: TLS 1.2+ with strong cipher suites via mkcert
- **Prod**: TLS 1.2+ with Let's Encrypt, optional TLS 1.3 strict mode

### Resource Limits (Production)

| Service          | Memory | CPU |
| ---------------- | ------ | --- |
| api-gateway      | 512MB  | 1.0 |
| ai-service       | 1GB    | 2.0 |
| plugin-service   | 512MB  | 1.0 |
| workflow-service | 512MB  | 1.0 |
| vector-service   | 1GB    | 2.0 |

## File Structure

```
infra/
├── proxy/
│   ├── traefik.yml              # Static Traefik configuration
│   └── dynamic/
│       ├── tls.yml              # TLS certificates & cipher suites
│       └── middlewares.yml      # Security middlewares
├── certs/                        # Generated SSL certs (gitignored)
│   ├── nemo.local+4.pem
│   └── nemo.local+4-key.pem
├── grafana/                      # Grafana provisioning
├── loki/                         # Loki configuration
├── prometheus/                   # Prometheus configuration
└── promtail/                     # Promtail configuration

scripts/
├── setup-dev.sh                  # Full dev environment setup
├── setup-certs.sh                # SSL certificate generation
└── protect-main.sh               # GitHub branch protection
```
