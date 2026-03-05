# ==============================================================================
# Nemo Platform — Root Makefile
# ==============================================================================

.PHONY: help dev-up dev-down proto build test lint clean

DOCKER_COMPOSE = docker compose -f docker-compose.yml
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
# Docker Compose
# ==============================================================================

dev-up: ## Start all services in development mode
	$(DOCKER_COMPOSE) up --build -d

dev-down: ## Stop all services
	$(DOCKER_COMPOSE) down -v

dev-logs: ## Tail logs for all services
	$(DOCKER_COMPOSE) logs -f

dev-ps: ## Show running services
	$(DOCKER_COMPOSE) ps

infra-up: ## Start only infrastructure (DB, Redis, Kafka, etc.)
	$(DOCKER_COMPOSE) up -d postgres redis chromadb kafka zookeeper

infra-down: ## Stop infrastructure
	$(DOCKER_COMPOSE) down -v postgres redis chromadb kafka zookeeper

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
	$(DOCKER_COMPOSE) build

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
