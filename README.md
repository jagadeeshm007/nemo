# Nemo — Agentic RAG Assistant Platform

> Enterprise-grade AI assistant platform with multi-LLM orchestration, RAG document intelligence, plugin ecosystem, and multi-stage workflow execution.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (Next.js)                          │
│  Chat UI │ Model Config │ Plugin Mgmt │ Workflow Monitor │ Uploads  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ HTTPS / WSS / SSE
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      API GATEWAY (Go / gRPC-Gateway)                │
│  Auth │ Rate Limiting │ Request Routing │ Session Mgmt │ Streaming  │
└───┬──────────┬──────────┬──────────┬──────────┬─────────────────────┘
    │ gRPC     │ gRPC     │ gRPC     │ gRPC     │
    ▼          ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│   AI   │ │Plugin  │ │Workflow│ │Vector  │ │ Auth   │
│Service │ │Service │ │Service │ │Service │ │Service │
│(Python)│ │(Python)│ │(Python)│ │(Python)│ │ (Go)   │
└───┬────┘ └───┬────┘ └───┬────┘ └───┬────┘ └────────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        EVENT BUS (Kafka)                            │
│  DocumentUploaded │ EmbeddingGenerated │ QueryRequested │ ...       │
└─────────────────────────────────────────────────────────────────────┘
    │          │          │          │
    ▼          ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐
│Postgres│ │ChromaDB│ │ Redis  │ │  Loki  │
│        │ │        │ │        │ │Grafana │
└────────┘ └────────┘ └────────┘ └────────┘
```

## Services

| Service            | Language           | Responsibility                                               |
| ------------------ | ------------------ | ------------------------------------------------------------ |
| `frontend`         | TypeScript/Next.js | Chat UI, config management, monitoring dashboards            |
| `api-gateway`      | Go                 | Authentication, rate limiting, request routing, gRPC gateway |
| `ai-service`       | Python/FastAPI     | LLM orchestration, agent reasoning, tool execution           |
| `plugin-service`   | Python/FastAPI     | Plugin lifecycle, registry, execution                        |
| `workflow-service` | Python/FastAPI     | Multi-stage workflow orchestration, state management         |
| `vector-service`   | Python/FastAPI     | Document ingestion, embedding, vector search                 |

## Quick Start

```bash
# Clone and start all services
make dev-up

# Or start individually
make gateway
make ai-service
make frontend
```

## Development

```bash
# Generate protobuf files
make proto

# Run tests
make test

# Lint all services
make lint
```

## Configuration

All configuration is externalized via YAML files in `configs/`:

- `configs/models.yaml` — LLM provider configuration
- `configs/plugins.yaml` — Plugin registry and settings
- `configs/workflows.yaml` — Workflow definitions
- `configs/gateway.yaml` — API gateway settings

## Documentation

- [Architecture Decision Records](docs/adr/)
- [API Documentation](docs/api/)
- [Deployment Guide](docs/deployment/)
- [Plugin Development Guide](docs/plugins/)

## License

Proprietary — All rights reserved.
