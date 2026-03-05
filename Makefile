# ==============================================================================
# Nemo Platform — Root Makefile
# ==============================================================================

.PHONY: help dev-up dev-down dev-logs dev-ps prod-up prod-down \
       infra-up infra-down proto build test lint clean setup

# Compose commands
COMPOSE_BASE = docker compose -f docker-compose.base.yml
COMPOSE_DEV  = $(COMPOSE_BASE) -f docker-compose.dev.yml --env-file .env.dev
COMPOSE_PROD = $(COMPOSE_BASE) -f docker-compose.prod.yml --env-file .env.prod

# Legacy single-file (kept for backward compat)
COMPOSE_LEGACY = docker compose -f docker-compose.yml

PROTO_DIR = proto
GATEWAY_DIR = services/api-gateway
AI_DIR = services/ai-service
PLUGIN_DIR = services/plugin-service
WORKFLOW_DIR = services/workflow-service
VECTOR_DIR = services/vector-service
FRONTEND_DIR = services/frontend

# ==============================================================================
# Help
# ==============================================================================

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ==============================================================================
# Setup
# ==============================================================================

setup: ## First-time dev environment setup (hosts, certs, env)
	@bash scripts/setup-dev.sh

# ==============================================================================
# Docker Compose — Development
# ==============================================================================

dev-up: ## Start all services in development mode
	$(COMPOSE_DEV) up --build -d

dev-down: ## Stop all dev services
	$(COMPOSE_DEV) down -v

dev-logs: ## Tail logs for all services
	$(COMPOSE_DEV) logs -f

dev-ps: ## Show running services
	$(COMPOSE_DEV) ps

infra-up: ## Start only infrastructure (DB, Redis, Kafka, etc.)
	$(COMPOSE_DEV) up -d postgres redis chromadb kafka zookeeper traefik

infra-down: ## Stop infrastructure
	$(COMPOSE_DEV) down -v postgres redis chromadb kafka zookeeper traefik

# ==============================================================================
# Docker Compose — Production
# ==============================================================================

prod-up: ## Start all services in production mode
	$(COMPOSE_PROD) up --build -d

prod-down: ## Stop all production services
	$(COMPOSE_PROD) down

prod-logs: ## Tail production logs
	$(COMPOSE_PROD) logs -f

# ==============================================================================
# Docker Compose — Legacy (single docker-compose.yml)
# ==============================================================================

legacy-up: ## Start using legacy single compose file
	$(COMPOSE_LEGACY) up --build -d

legacy-down: ## Stop legacy compose
	$(COMPOSE_LEGACY) down -v

# ==============================================================================
# Protobuf
# ==============================================================================

proto: ## Generate protobuf code for all services
	@echo "Generating Go protobuf..."
	cd $(GATEWAY_DIR) && make proto
	@echo "Generating Python protobuf..."
	cd $(AI_DIR) && make proto
	@echo "Proto generation complete."

# ==============================================================================
# Build
# ==============================================================================

build: ## Build all Docker images
	$(COMPOSE_DEV) build

build-gateway: ## Build API Gateway
	cd $(GATEWAY_DIR) && make build

build-ai: ## Build AI Service
	cd $(AI_DIR) && make build

build-frontend: ## Build Frontend
	cd $(FRONTEND_DIR) && npm run build

# ==============================================================================
# Test
# ==============================================================================

test: ## Run tests for all services
	cd $(GATEWAY_DIR) && make test
	cd $(AI_DIR) && make test
	cd $(PLUGIN_DIR) && make test
	cd $(WORKFLOW_DIR) && make test
	cd $(VECTOR_DIR) && make test

test-gateway: ## Run gateway tests
	cd $(GATEWAY_DIR) && make test

test-ai: ## Run AI service tests
	cd $(AI_DIR) && make test

# ==============================================================================
# Lint
# ==============================================================================

lint: ## Lint all services
	cd $(GATEWAY_DIR) && make lint
	cd $(AI_DIR) && make lint
	cd $(FRONTEND_DIR) && npm run lint

# ==============================================================================
# Database
# ==============================================================================

db-migrate: ## Run database migrations
	cd $(GATEWAY_DIR) && make migrate-up

db-rollback: ## Rollback last migration
	cd $(GATEWAY_DIR) && make migrate-down

db-seed: ## Seed database with sample data
	cd $(GATEWAY_DIR) && make seed

# ==============================================================================
# Clean
# ==============================================================================

clean: ## Clean all build artifacts
	cd $(GATEWAY_DIR) && make clean
	cd $(AI_DIR) && make clean
	cd $(FRONTEND_DIR) && rm -rf .next node_modules
	docker system prune -f
