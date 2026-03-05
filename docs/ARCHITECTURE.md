# Nemo — System Architecture Document

## 1. High-Level System Architecture

Nemo is a cloud-native, event-driven, microservices-based AI assistant platform.
It follows clean architecture principles with strict separation of concerns.

### Design Principles

- **Config-driven**: No hardcoded providers, plugins, or workflows
- **Event-driven**: Kafka-based async communication for decoupled services
- **Plugin-first**: All tools/integrations are plugins with standard lifecycle
- **Factory pattern**: LLM providers instantiated via factory, never directly
- **Observable**: Every service emits structured logs, metrics, and traces
- **Resilient**: Graceful degradation, circuit breakers, retry policies

## 2. Microservice Architecture

```
                                    ┌──────────────┐
                                    │   Frontend   │
                                    │  (Next.js)   │
                                    └──────┬───────┘
                                           │ REST/SSE/WS
                                           ▼
                                    ┌──────────────┐
                              ┌────▶│ API Gateway  │◀────┐
                              │     │    (Go)      │     │
                              │     └──┬───┬───┬───┘     │
                              │        │   │   │         │
                    ┌─────────┘   gRPC │   │   │ gRPC   └─────────┐
                    │                  │   │   │                   │
              ┌─────▼─────┐    ┌──────▼┐  │  ┌▼──────┐    ┌──────▼─────┐
              │  Plugin   │    │  AI   │  │  │Vector │    │  Workflow  │
              │  Service  │    │Service│  │  │Service│    │  Service   │
              │ (Python)  │    │(Py)   │  │  │(Py)   │    │  (Python)  │
              └─────┬─────┘    └───┬───┘  │  └───┬───┘    └──────┬─────┘
                    │              │       │      │               │
                    └──────────────┼───────┼──────┼───────────────┘
                                   │       │      │
                            ┌──────▼───────▼──────▼──────┐
                            │        Kafka (Events)       │
                            └──────┬───────┬──────┬──────┘
                                   │       │      │
                    ┌──────────────┼───────┼──────┼──────────────┐
                    │              │       │      │              │
              ┌─────▼─────┐ ┌─────▼──┐ ┌──▼────┐ ┌▼─────┐ ┌────▼────┐
              │ PostgreSQL│ │ChromaDB│ │ Redis │ │ Loki │ │Prometheus│
              └───────────┘ └────────┘ └───────┘ └──────┘ └─────────┘
```

## 3. Service Responsibilities

### API Gateway (Go)

- HTTP/REST to gRPC translation
- JWT authentication and authorization
- Rate limiting (token bucket via Redis)
- Request routing and load balancing
- SSE/WebSocket proxy for streaming
- Request/response logging
- CORS and security headers
- Health checks and readiness probes

### AI Service (Python/FastAPI)

- LLM Factory — dynamic model instantiation
- Agent reasoning loop (ReAct pattern)
- Tool selection and execution orchestration
- Conversation memory management
- Prompt template management
- Streaming response generation
- Context window management
- Model fallback and retry logic

### Plugin Service (Python/FastAPI)

- Plugin registry and discovery
- Plugin lifecycle (install, activate, deactivate, uninstall)
- Plugin configuration management
- Plugin permission enforcement
- Plugin execution sandbox
- Plugin versioning
- Plugin health monitoring

### Workflow Service (Python/FastAPI)

- Workflow definition parsing (YAML/DB)
- Multi-stage execution orchestration
- Step dependency resolution
- Workflow state persistence
- Retry and error handling
- Workflow monitoring and reporting
- Conditional branching
- Parallel step execution

### Vector Service (Python/FastAPI)

- Document ingestion (PDF, DOCX, TXT, MD, CSV)
- Text chunking strategies
- Embedding generation (via LLM Factory)
- Vector storage (ChromaDB)
- Semantic search / similarity search
- Index management
- Document metadata management

## 4. LLM Factory Architecture

```
┌─────────────────────────────────────────┐
│              LLMFactory                  │
│                                          │
│  + create(provider, model, config)       │
│  + list_providers() -> List[Provider]    │
│  + get_provider(name) -> LLMProvider     │
│  + register_provider(provider)           │
└──────────────────┬──────────────────────┘
                   │
         ┌─────────┼─────────┐
         │         │         │
    ┌────▼───┐ ┌───▼────┐ ┌─▼──────┐
    │OpenAI  │ │Claude  │ │Gemini  │
    │Provider│ │Provider│ │Provider│
    └────────┘ └────────┘ └────────┘
         │         │         │
    ┌────▼─────────▼─────────▼──────┐
    │       LLMProvider Interface    │
    │                                │
    │  + complete(prompt, opts)      │
    │  + stream(prompt, opts)        │
    │  + embed(text)                 │
    │  + get_models() -> List[Model] │
    │  + health_check() -> bool      │
    └────────────────────────────────┘
```

### Configuration (models.yaml)

```yaml
providers:
  - name: openai
    enabled: true
    api_key_env: OPENAI_API_KEY
    models:
      - id: gpt-4o
        enabled: true
        max_tokens: 128000
        default: true
      - id: gpt-4o-mini
        enabled: true
        max_tokens: 128000
  - name: anthropic
    enabled: true
    api_key_env: ANTHROPIC_API_KEY
    models:
      - id: claude-sonnet-4-20250514
        enabled: true
        max_tokens: 200000
  - name: google
    enabled: false
    api_key_env: GOOGLE_API_KEY
    models:
      - id: gemini-2.0-flash
        enabled: true
        max_tokens: 1048576
```

## 5. Plugin System Architecture

```
┌──────────────────────────────────────────┐
│            PluginManager                  │
│                                           │
│  + register(plugin_manifest)              │
│  + activate(plugin_id)                    │
│  + deactivate(plugin_id)                  │
│  + execute(plugin_id, action, params)     │
│  + get_config(plugin_id)                  │
│  + update_config(plugin_id, config)       │
│  + list_plugins() -> List[PluginInfo]     │
└──────────────────┬───────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
┌───▼────┐  ┌─────▼────┐  ┌─────▼────┐
│Calendar│  │  Slack   │  │  Search  │
│Plugin  │  │  Plugin  │  │  Plugin  │
└────────┘  └──────────┘  └──────────┘
    │              │              │
┌───▼──────────────▼──────────────▼──┐
│         PluginInterface            │
│                                    │
│  + metadata() -> PluginMetadata    │
│  + configure(config)               │
│  + execute(action, params)         │
│  + health() -> HealthStatus        │
│  + schema() -> ActionSchema        │
└────────────────────────────────────┘
```

### Plugin Manifest

```yaml
id: google-calendar
name: Google Calendar
version: 1.0.0
description: Integration with Google Calendar
author: Nemo Team
permissions:
  - calendar:read
  - calendar:write
config_schema:
  credentials_path:
    type: string
    required: true
  default_calendar:
    type: string
    default: primary
actions:
  - name: list_events
    description: List upcoming events
    parameters:
      max_results:
        type: integer
        default: 10
  - name: create_event
    description: Create a calendar event
    parameters:
      title:
        type: string
        required: true
      start_time:
        type: datetime
        required: true
      end_time:
        type: datetime
        required: true
```

## 6. Agent Workflow Architecture

```
User Query
    │
    ▼
┌────────────────┐
│  Parse Intent  │
└───────┬────────┘
        │
        ▼
┌────────────────┐     ┌──────────────┐
│  LLM Reasoning │────▶│  Tool Select │
│  (ReAct Loop)  │◀────│              │
└───────┬────────┘     └──────────────┘
        │
        ▼
┌────────────────┐
│ Tool Execution │──────┐
└───────┬────────┘      │
        │               │ Multiple tools
        ▼               │ may execute
┌────────────────┐      │
│Context Update  │◀─────┘
└───────┬────────┘
        │
        ▼
┌────────────────┐     ┌──────────────┐
│  Continue?     │─Yes▶│ Next Tool    │
│  (LLM decides) │     │ Iteration    │
└───────┬────────┘     └──────────────┘
        │ No
        ▼
┌────────────────┐
│ Final Response │
│ Generation     │
└───────┬────────┘
        │
        ▼
   Stream to User
```

## 7. Kafka Event Design

### Topics

| Topic                        | Producer         | Consumer(s)                      | Description                  |
| ---------------------------- | ---------------- | -------------------------------- | ---------------------------- |
| `nemo.documents.uploaded`    | vector-service   | ai-service, workflow-service     | Document upload notification |
| `nemo.embeddings.generated`  | vector-service   | ai-service                       | Embedding completion         |
| `nemo.queries.requested`     | api-gateway      | ai-service                       | New query from user          |
| `nemo.tools.executed`        | ai-service       | workflow-service, plugin-service | Tool execution result        |
| `nemo.workflows.completed`   | workflow-service | ai-service, api-gateway          | Workflow done                |
| `nemo.workflows.failed`      | workflow-service | ai-service, api-gateway          | Workflow error               |
| `nemo.plugins.state_changed` | plugin-service   | api-gateway                      | Plugin activated/deactivated |
| `nemo.models.config_changed` | ai-service       | api-gateway                      | Model config update          |
| `nemo.audit.events`          | all services     | audit-consumer                   | Audit trail                  |
| `nemo.metrics.events`        | all services     | prometheus-exporter              | Custom metrics               |

### Event Schema (Avro-compatible JSON)

```json
{
  "event_id": "uuid",
  "event_type": "DocumentUploaded",
  "timestamp": "2026-03-05T10:00:00Z",
  "source_service": "vector-service",
  "correlation_id": "uuid",
  "payload": {
    "document_id": "uuid",
    "filename": "report.pdf",
    "size_bytes": 1048576,
    "mime_type": "application/pdf",
    "user_id": "uuid"
  },
  "metadata": {
    "trace_id": "uuid",
    "span_id": "uuid"
  }
}
```

## 8. Database Schema Overview

### PostgreSQL Tables

- `users` — User accounts and profiles
- `conversations` — Chat sessions
- `messages` — Individual messages within conversations
- `models` — LLM provider and model configuration
- `plugins` — Plugin registry and state
- `plugin_configs` — Plugin configuration key-value store
- `workflows` — Workflow definitions
- `workflow_runs` — Workflow execution instances
- `workflow_steps` — Individual steps within workflow runs
- `documents` — Uploaded document metadata
- `audit_logs` — System audit trail

### Redis Keys

- `session:{user_id}` — User session data (TTL: 24h)
- `rate:{user_id}:{endpoint}` — Rate limiting counters (TTL: 60s)
- `cache:response:{hash}` — Response cache (TTL: 5m)
- `workflow:state:{run_id}` — Active workflow state (TTL: 1h)
- `model:config` — Cached model configuration (TTL: 10m)
- `plugin:state:{plugin_id}` — Plugin runtime state (TTL: 30m)

## 9. Observability Architecture

```
┌──────────────┐     ┌───────────────┐     ┌──────────┐
│  Services    │────▶│   Promtail    │────▶│   Loki   │
│ (structured  │     │ (log shipper) │     │(log store)│
│   JSON logs) │     └───────────────┘     └────┬─────┘
└──────┬───────┘                                │
       │                                        ▼
       │ /metrics                         ┌──────────┐
       └─────────────────────────────────▶│ Grafana  │
                                          │(dashboards)│
┌──────────────┐     ┌───────────────┐    └────┬─────┘
│  Services    │────▶│  Prometheus   │─────────┘
│ (/metrics)   │     │  (scraper)    │
└──────────────┘     └───────────────┘
```

## 10. Docker Architecture

Each service runs in its own container. Docker Compose orchestrates local development.

| Container        | Base Image                      | Ports      | Depends On             |
| ---------------- | ------------------------------- | ---------- | ---------------------- |
| frontend         | node:20-alpine                  | 3000       | api-gateway            |
| api-gateway      | golang:1.22-alpine              | 8080, 9090 | redis, postgres        |
| ai-service       | python:3.12-slim                | 8001       | redis, postgres, kafka |
| plugin-service   | python:3.12-slim                | 8002       | postgres, kafka        |
| workflow-service | python:3.12-slim                | 8003       | postgres, redis, kafka |
| vector-service   | python:3.12-slim                | 8004       | chromadb, kafka        |
| postgres         | postgres:16-alpine              | 5432       | —                      |
| redis            | redis:7-alpine                  | 6379       | —                      |
| chromadb         | chromadb/chroma:latest          | 8005       | —                      |
| kafka            | confluentinc/cp-kafka:7.6.0     | 9092       | zookeeper              |
| zookeeper        | confluentinc/cp-zookeeper:7.6.0 | 2181       | —                      |
| prometheus       | prom/prometheus:latest          | 9091       | —                      |
| grafana          | grafana/grafana:latest          | 3001       | prometheus, loki       |
| loki             | grafana/loki:latest             | 3100       | —                      |
| promtail         | grafana/promtail:latest         | —          | loki                   |
