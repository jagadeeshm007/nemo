# Nemo — Agentic RAG Assistant Platform

> Enterprise-grade AI assistant platform with multi-LLM orchestration, RAG document intelligence, plugin ecosystem, durable workflow execution, and full-stack observability — powered by a microservices architecture running on Kubernetes with GitOps deployment.

---

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Application Services](#application-services)
  - [Frontend (Next.js 14)](#1-frontend--nextjs-14)
  - [API Gateway (Go)](#2-api-gateway--go--gin--grpc-gateway)
  - [AI Service (Python)](#3-ai-service--python--fastapi)
  - [Plugin Service (Python)](#4-plugin-service--python--fastapi)
  - [Workflow Service (Python)](#5-workflow-service--python--fastapi)
  - [Vector Service (Python)](#6-vector-service--python--fastapi)
- [Enterprise Infrastructure](#enterprise-infrastructure)
  - [Temporal — Workflow Orchestration](#7-temporal--workflow-orchestration)
  - [Kafka — Event-Driven Architecture](#8-apache-kafka--event-driven-architecture)
  - [OpenTelemetry + Grafana Tempo — Distributed Tracing](#9-opentelemetry-collector--grafana-tempo--distributed-tracing)
  - [HashiCorp Vault — Secrets Management](#10-hashicorp-vault--secrets-management)
  - [Elasticsearch — Hybrid Search](#11-elasticsearch--hybrid-search)
  - [Model Gateway — LLM Routing](#12-model-gateway--llm-routing--factory-pattern)
  - [Unleash — Feature Flags](#13-unleash--feature-flags)
  - [Keycloak — Identity & Access Management](#14-keycloak--identity--access-management)
- [Data Stores](#data-stores)
  - [PostgreSQL](#15-postgresql-16)
  - [Redis](#16-redis-7)
  - [ChromaDB](#17-chromadb)
- [Observability Stack](#observability-stack)
  - [Prometheus](#18-prometheus)
  - [Grafana](#19-grafana)
  - [Loki + Promtail](#20-loki--promtail)
- [Networking & Security](#networking--security)
  - [Traefik Reverse Proxy](#21-traefik--reverse-proxy--tls-termination)
- [gRPC / Protobuf Contracts](#grpc--protobuf-contracts)
- [Infrastructure as Code (Terraform)](#infrastructure-as-code--terraform)
- [Kubernetes Deployment](#kubernetes-deployment)
- [Argo CD — GitOps](#argo-cd--gitops-continuous-delivery)
- [CI/CD Pipelines](#cicd-pipelines)
- [Configuration Files](#configuration-files)
- [Quick Start](#quick-start)
- [Endpoints](#endpoints)

---

## Architecture Overview

```
                                    ┌──────────────────────┐
                                    │   Keycloak (IAM)     │
                                    │ OAuth2 / OIDC / SSO  │
                                    └──────────┬───────────┘
                                               │ JWT
┌──────────────────────────────────────────────────────────────────────────┐
│                          FRONTEND (Next.js 14)                           │
│   Chat UI │ Model Config │ Plugin Mgmt │ Workflow Monitor │ Doc Upload   │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │ HTTPS / WSS / SSE
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    TRAEFIK (Reverse Proxy + TLS 1.3)                     │
│         Rate Limiting │ CORS │ Compression │ Secure Headers              │
└────────────────────────────────┬─────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY (Go / Gin / gRPC-Gateway)                 │
│ Auth │ Rate Limiting │ Request Routing │ Session Mgmt │ Streaming │ RBAC │
└──┬───────────┬───────────┬───────────┬───────────┬───────────────────────┘
   │ gRPC      │ gRPC      │ gRPC      │ gRPC      │
   ▼           ▼           ▼           ▼           ▼
┌────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────────────┐
│   AI   │ │ Plugin  │ │Workflow │ │ Vector  │ │  Model Gateway  │
│Service │ │ Service │ │ Service │ │ Service │ │ (LLM Routing)   │
│(Python)│ │ (Python)│ │ (Python)│ │ (Python)│ │                 │
└──┬─────┘ └──┬──────┘ └──┬──────┘ └──┬──────┘ └──┬──────────────┘
   │          │           │           │            │
   ▼          ▼           ▼           ▼            ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         EVENT BUS (Apache Kafka)                         │
│ DocumentUploaded │ EmbeddingGenerated │ QueryRequested │ WorkflowStep   │
└──────────────────────────────────────────────────────────────────────────┘
   │          │           │           │            │
   ▼          ▼           ▼           ▼            ▼
┌────────┐ ┌────────┐ ┌────────┐ ┌─────────────┐ ┌────────────┐
│Postgres│ │ChromaDB│ │ Redis  │ │Elasticsearch│ │  Temporal   │
│  (SQL) │ │(Vector)│ │(Cache) │ │  (Keyword)  │ │ (Durable)  │
└────────┘ └────────┘ └────────┘ └─────────────┘ └────────────┘
   │          │           │           │            │
   └──────────┴───────────┴───────────┴────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         OBSERVABILITY                                    │
│  Prometheus │ Grafana │ Loki │ Tempo │ OTel Collector │ Promtail        │
└──────────────────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                     SECURITY & OPERATIONS                                │
│   HashiCorp Vault (Secrets) │ Unleash (Feature Flags) │ Keycloak (IAM)  │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Application Services

### 1. Frontend — Next.js 14

| Property | Value                                     |
| -------- | ----------------------------------------- |
| **Tech** | Next.js 14.2.5, TypeScript 5.5.3, Node 20 |
| **Port** | 3000                                      |
| **URL**  | `https://nemo.local`                      |

The **frontend** is a server-side rendered React application built with Next.js 14 and TypeScript. It provides the primary user interface for the entire Nemo platform.

**Capabilities:**

- **Chat Interface** — Real-time conversational AI with streaming responses via Server-Sent Events (SSE) and WebSockets. Supports multi-turn conversations with context retention, markdown rendering, code syntax highlighting, and file attachments.
- **Model Configuration** — Visual interface for selecting and configuring LLM providers (OpenAI, Anthropic, Google), adjusting temperature/top-p/max-tokens parameters, and switching between fallback chains (default, fast, reasoning).
- **Plugin Management** — Browse, install, configure, and monitor plugins. Visual plugin marketplace with capability descriptions, version management, and per-user enable/disable toggles.
- **Workflow Monitor** — Real-time visualization of multi-stage workflow execution, including Temporal workflow status, step-by-step progress tracking, retry history, and failure diagnostics.
- **Document Upload & RAG** — Drag-and-drop document ingestion supporting PDF, DOCX, TXT, and Markdown. Progress indicators for chunking, embedding generation, and vector store indexing.
- **Keycloak SSO Integration** — OAuth2/OIDC authentication via Keycloak. Users sign in through the Keycloak login page, and the frontend receives JWT tokens for API authorization. Role-based UI rendering (admin sees management panels, users see chat).
- **Feature Flag Awareness** — Integrates with Unleash frontend SDK to dynamically show/hide features based on feature flag state without redeployment.

---

### 2. API Gateway — Go / Gin / gRPC-Gateway

| Property  | Value                    |
| --------- | ------------------------ |
| **Tech**  | Go 1.22, Gin framework   |
| **Ports** | 8080 (HTTP), 9090 (gRPC) |
| **URL**   | `https://api.nemo.local` |

The **API Gateway** is the single entry point for all client requests. Written in Go for maximum performance, it handles authentication, authorization, rate limiting, and intelligent request routing to backend microservices.

**Capabilities:**

- **Authentication & Authorization** — Validates JWT tokens issued by Keycloak. Extracts user identity, roles (admin/user/viewer), and permissions from the token. Enforces RBAC policies — e.g., only admins can manage plugins; viewers have read-only chat access.
- **Rate Limiting** — Configurable per-user and per-IP rate limiting (default: 100 req/s). Uses Redis as the backing store for distributed rate limit counters, ensuring consistent enforcement across multiple gateway instances.
- **Request Routing** — Routes incoming HTTP/REST requests to the appropriate backend microservice via gRPC. The gateway translates REST calls to gRPC using protobuf service definitions, supporting both unary and streaming RPCs.
- **gRPC-Gateway** — Dual-protocol support: clients can connect via HTTP/REST (port 8080) or native gRPC (port 9090). The HTTP endpoint auto-translates to gRPC internally, giving browser clients REST access while inter-service communication uses efficient gRPC.
- **Session Management** — Maintains user sessions in Redis with configurable TTL. Tracks active conversations, user preferences, and model selections across requests.
- **Streaming Support** — Proxies SSE and WebSocket connections for real-time LLM response streaming from backend services to the frontend.
- **Health & Metrics** — Exposes `/health` for liveness/readiness probes and `/metrics` in Prometheus format with request count, latency histograms, error rates, and active connection gauges.
- **OpenTelemetry Instrumentation** — Automatically generates distributed traces for every request, propagating trace context (W3C Trace Context) to all downstream gRPC calls. Exports spans to the OTel Collector.

---

### 3. AI Service — Python / FastAPI

| Property | Value                      |
| -------- | -------------------------- |
| **Tech** | Python 3.12, FastAPI, gRPC |
| **Port** | 8001                       |
| **gRPC** | 50051                      |

The **AI Service** is the intelligence core of the platform. It orchestrates interactions with multiple LLM providers, implements agentic reasoning loops, and coordinates tool execution with other services.

**Capabilities:**

- **Multi-LLM Orchestration** — Connects to OpenAI (GPT-4o, GPT-4o-mini, o1), Anthropic (Claude 3.5 Sonnet, Claude 3 Haiku), and Google (Gemini 1.5 Pro, Gemini 1.5 Flash). Selects the optimal model based on the configured fallback chain and request parameters.
- **Agentic Reasoning** — Implements ReAct (Reasoning + Acting) loops where the LLM can reason about a query, decide to invoke tools (plugins), observe results, and iterate until a satisfactory answer is produced. Supports multi-step reasoning chains with configurable iteration limits.
- **Tool Execution** — Coordinates with the Plugin Service to execute external tools (web search, calendar access, Slack integration). Formats tool results as context for the LLM's next reasoning step.
- **RAG Pipeline** — For knowledge-grounded queries, retrieves relevant document chunks from the Vector Service using hybrid search (vector similarity + keyword matching via Elasticsearch). Injects retrieved context into the LLM prompt with source attribution.
- **Streaming Responses** — Streams LLM completions token-by-token to the API Gateway via gRPC server streaming, enabling real-time response rendering in the frontend.
- **Conversation Memory** — Maintains conversation history in PostgreSQL with configurable context window management. Supports sliding window, summary-based, and token-count-based memory strategies.
- **Temporal Integration** — For complex multi-step tasks, delegates execution to Temporal durable workflows, enabling retry-safe, long-running operations that survive service restarts.
- **Cost Tracking** — Records token usage and estimated cost per request, per model, per user. Enforces configurable daily spend limits ($100/day default) and per-request cost caps ($5/request default) via the Model Gateway config.

---

### 4. Plugin Service — Python / FastAPI

| Property | Value                      |
| -------- | -------------------------- |
| **Tech** | Python 3.12, FastAPI, gRPC |
| **Port** | 8002                       |
| **gRPC** | 50052                      |

The **Plugin Service** manages the lifecycle and execution of external tool integrations that extend the AI's capabilities beyond its training data.

**Capabilities:**

- **Plugin Registry** — Maintains a catalog of available plugins with metadata: name, description, version, input/output schemas (JSON Schema), capability tags, and author information. Stored in PostgreSQL.
- **Plugin Lifecycle Management** — Handles plugin installation, configuration, versioning, enabling/disabling, and uninstallation. Supports per-user and per-organization plugin configurations.
- **Sandboxed Execution** — Executes plugin code in isolated environments with configurable timeouts (default: 30s), memory limits, and network access controls. Prevents malicious plugins from affecting the platform.
- **Built-in Plugins:**
  - **Web Search** — Searches the internet using configurable search providers and returns formatted results with snippets and URLs.
  - **Google Calendar** — Reads, creates, and modifies calendar events via Google Calendar API with OAuth2 user consent.
  - **Slack Integration** — Sends messages, reads channels, and responds to Slack events via Slack Bot API.
- **Feature Flag Gating** — Each plugin's availability is controlled by Unleash feature flags (e.g., `enable-google-calendar-plugin`, `enable-slack-plugin`), allowing gradual rollout and instant kill-switch capability.
- **Event Publishing** — Publishes plugin execution events to Kafka (`PluginExecuted`, `PluginFailed`) for audit logging and analytics.

---

### 5. Workflow Service — Python / FastAPI

| Property | Value                      |
| -------- | -------------------------- |
| **Tech** | Python 3.12, FastAPI, gRPC |
| **Port** | 8003                       |
| **gRPC** | 50053                      |

The **Workflow Service** orchestrates complex, multi-stage AI tasks that require sequential or parallel execution of multiple steps, with state persistence and failure recovery.

**Capabilities:**

- **Workflow Definitions** — Supports declarative workflow definitions (YAML-based) with steps, conditions, branching, loops, and parallel execution. Workflows are stored in PostgreSQL and versioned.
- **Temporal Durable Execution** — Delegates workflow execution to the Temporal server for durable, fault-tolerant processing. If the service crashes mid-workflow, Temporal automatically resumes from the last completed step on restart — no human intervention needed.
- **Built-in Workflow Types:**
  - **Research Agent** — Multi-step research: query decomposition → parallel web searches → result synthesis → answer generation with citations.
  - **Document Analysis** — Upload → chunking → embedding → indexing → summary generation → Q&A readiness.
  - **Task Execution Agent** — Break down complex user requests into subtasks, execute each via appropriate plugins, and combine results.
- **State Management** — Each workflow execution has a persistent state machine tracking current step, intermediate results, retry counts, and timing. Queryable via API for real-time progress monitoring.
- **Event-Driven Triggers** — Workflows can be triggered by Kafka events (e.g., a `DocumentUploaded` event auto-triggers the Document Analysis workflow).
- **Gradual Rollout** — New workflow types are gated behind feature flags (e.g., `enable-research-agent` at 100%, `enable-task-execution-agent` at 25% rollout) via Unleash.

---

### 6. Vector Service — Python / FastAPI

| Property | Value                      |
| -------- | -------------------------- |
| **Tech** | Python 3.12, FastAPI, gRPC |
| **Port** | 8004                       |
| **gRPC** | 50054                      |

The **Vector Service** handles document ingestion, embedding generation, and hybrid search — the core RAG (Retrieval-Augmented Generation) infrastructure.

**Capabilities:**

- **Document Ingestion** — Accepts PDF, DOCX, TXT, and Markdown files. Extracts text, applies intelligent chunking (recursive character splitting with configurable chunk size/overlap), and generates metadata (source, page number, section headers).
- **Embedding Generation** — Generates vector embeddings using configurable models (OpenAI `text-embedding-3-large`, Anthropic, or local models). Supports batch processing for bulk ingestion.
- **Dual-Store Indexing** — Indexes each document chunk in both:
  - **ChromaDB** (vector store) — for semantic similarity search using cosine distance.
  - **Elasticsearch** (keyword store) — for BM25 keyword matching with custom analyzers.
- **Hybrid Search** — Combines vector similarity search (ChromaDB) with keyword search (Elasticsearch) using Reciprocal Rank Fusion (RRF) with configurable weights (default: vector 0.6, keyword 0.4, k=60).
- **Cross-Encoder Reranking** — After initial retrieval, applies a cross-encoder model (`ms-marco-MiniLM-L-6-v2`) to rerank results for improved precision. Returns the top-k most relevant chunks (default: 10) with scores.
- **gRPC Hybrid Search Contract** — Exposes `Search`, `IndexDocument`, `DeleteDocument`, and `GetIndexStats` RPCs via the `HybridSearchService` proto definition. Supports vector-only, keyword-only, and hybrid search modes.
- **Kafka Integration** — Publishes `EmbeddingGenerated` events after successful indexing, enabling downstream services to react to new document availability.

---

## Enterprise Infrastructure

### 7. Temporal — Workflow Orchestration

| Property   | Value                           |
| ---------- | ------------------------------- |
| **Image**  | `temporalio/auto-setup:1.24`    |
| **UI**     | `temporalio/ui:2.26.2`          |
| **Port**   | 7233 (gRPC), 8088 (UI in dev)   |
| **URL**    | `https://temporal.nemo.local`   |
| **Config** | `infra/temporal/dynamicconfig/` |

**Temporal** is a durable execution engine that ensures long-running workflows survive infrastructure failures. Unlike traditional task queues, Temporal guarantees exactly-once execution semantics with automatic retries, timeouts, and state persistence.

**Why Temporal in Nemo:**

- **Durable Workflows** — A research agent workflow might take 5 minutes (decompose query → search 10 sources → synthesize). If the Workflow Service crashes at step 7, Temporal automatically resumes from step 7 on restart — no lost work, no duplicate API calls.
- **Retry Policies** — Configurable per-activity retry policies (e.g., retry LLM calls 3 times with exponential backoff on rate-limit errors).
- **Visibility** — The Temporal UI provides a searchable, sortable view of all workflow executions with timeline visualization, input/output inspection, and manual retry/cancel controls.
- **Namespace Isolation** — Nemo uses a dedicated `nemo` namespace in Temporal, isolating its workflows from other tenants.

**Configuration Details:**

- Uses PostgreSQL as the persistence backend (shares the Nemo database).
- Dynamic config (`development-sql.yaml`) tunes persistence QPS limits, task queue partitions, and history size limits.
- Auto-setup mode initializes the database schema on first start.

---

### 8. Apache Kafka — Event-Driven Architecture

| Property   | Value                             |
| ---------- | --------------------------------- |
| **Image**  | `confluentinc/cp-kafka:7.6.0`     |
| **Port**   | 9092 (external), 29092 (internal) |
| **Config** | `events/schemas.yaml`             |

**Apache Kafka** serves as the event backbone for the entire platform, enabling asynchronous, decoupled communication between microservices via publish-subscribe messaging.

**Event Topics & Schema:**

- `document.uploaded` — Fired when a user uploads a new document. Triggers the ingestion and embedding pipeline in the Vector Service.
- `embedding.generated` — Fired after document chunks are embedded and indexed. Signals RAG readiness to the AI Service.
- `query.requested` — Records every user query for analytics, audit logging, and billing.
- `workflow.step.completed` — Emitted by the Workflow Service after each workflow step completes. Enables real-time progress tracking.
- `plugin.executed` / `plugin.failed` — Audit trail for all plugin invocations.
- `model.completion` — Records LLM completions with token counts, latency, cost, and provider info.

**Architecture Role:**

- Decouples producers from consumers — the AI Service doesn't need to know about logging or analytics systems.
- Enables replay — if a new analytics service is added, it can replay historical events from Kafka.
- Provides backpressure — if the Vector Service is overloaded, Kafka buffers incoming documents without dropping them.
- Zookeeper-managed (ZK 2181) for broker coordination and partition management.

---

### 9. OpenTelemetry Collector + Grafana Tempo — Distributed Tracing

| Property         | Value                                         |
| ---------------- | --------------------------------------------- |
| **OTel Image**   | `otel/opentelemetry-collector-contrib:0.96.0` |
| **Tempo Image**  | `grafana/tempo:2.4.1`                         |
| **OTel Config**  | `infra/otel/otel-collector.yml`               |
| **Tempo Config** | `infra/tempo/tempo.yml`                       |

**OpenTelemetry (OTel) Collector** is a vendor-neutral telemetry pipeline that receives traces, metrics, and logs from all application services and routes them to the appropriate backend.

**Grafana Tempo** is a high-scale, cost-effective distributed tracing backend that stores and queries trace data.

**How It Works:**

1. Every application service is instrumented with OpenTelemetry SDKs. When a user sends a chat request, the API Gateway creates a root trace span and propagates the trace context (W3C `traceparent` header) to every downstream gRPC call.
2. Each service adds its own spans — the AI Service adds spans for LLM calls, the Vector Service adds spans for embedding lookups and hybrid search, the Plugin Service adds spans for tool execution.
3. All spans are exported to the **OTel Collector** via OTLP (gRPC on port 4317, HTTP on port 4318).
4. The OTel Collector processes spans through a pipeline:
   - **Memory Limiter** — prevents OOM by capping memory usage at 512MB.
   - **Resource Processor** — enriches spans with `service.namespace=nemo` and `deployment.environment`.
   - **Attributes Processor** — scrubs sensitive headers (`authorization`, `cookie`, `x-api-key`) from span attributes.
   - **Batch Processor** — batches spans for efficient export (200ms timeout, 512 batch size).
5. Processed spans are exported to **Tempo** for storage and querying.
6. Tempo stores traces in a local volume (dev) or S3 (production) with configurable retention.

**Three Telemetry Pipelines:**

- **Traces** → OTel Collector → Tempo (query via Grafana)
- **Metrics** → OTel Collector → Prometheus (remote write)
- **Logs** → OTel Collector → Loki

**Grafana Integration:**

- The Tempo datasource in Grafana supports trace-to-logs (click a span → see correlated Loki logs) and trace-to-metrics (click a span → see Prometheus metrics for that service).
- A dedicated **Distributed Tracing dashboard** shows: service map, trace search, p50/p95/p99 latencies by service, error rates, and OTel Collector health.

---

### 10. HashiCorp Vault — Secrets Management

| Property     | Value                               |
| ------------ | ----------------------------------- |
| **Image**    | `hashicorp/vault:1.16`              |
| **Port**     | 8200                                |
| **URL**      | `https://vault.nemo.local`          |
| **Config**   | `infra/vault/config/vault.hcl`      |
| **Policies** | `infra/vault/policies/nemo-app.hcl` |

**HashiCorp Vault** provides centralized, audited secrets management — replacing hardcoded API keys and passwords with dynamically retrieved, short-lived credentials.

**How Nemo Uses Vault:**

- **KV v2 Secrets Engine** — All application secrets are stored at `secret/data/nemo/*` with versioning:
  - `secret/data/nemo/database` — PostgreSQL credentials (host, port, user, password).
  - `secret/data/nemo/redis` — Redis connection URL and password.
  - `secret/data/nemo/kafka` — Kafka broker addresses and SASL credentials.
  - `secret/data/nemo/llm` — LLM provider API keys (OpenAI, Anthropic, Google).
  - `secret/data/nemo/auth` — JWT signing key and HMAC secrets.
  - `secret/data/nemo/oauth` — Keycloak client secret and OIDC configuration.

- **AppRole Authentication** — Services authenticate to Vault using AppRole (role-id + secret-id), not long-lived tokens. The `nemo-app` role provides read-only access to `secret/data/nemo/*`.

- **Kubernetes Integration** — In production (EKS), services use the Vault Agent Injector with Kubernetes service account authentication. Vault Agent runs as a sidecar, automatically fetches secrets, and renders them to files that the application reads — zero code changes needed.

- **Audit Logging** — Every secret access is logged with timestamp, accessor identity, and path. Useful for compliance audits and detecting unauthorized access.

**Development Workflow:**

- The init script (`infra/vault/scripts/init-dev.sh`) automatically initializes Vault, unseals it, enables the KV v2 engine, writes all development secrets, and configures the AppRole.

---

### 11. Elasticsearch — Hybrid Search

| Property   | Value                                   |
| ---------- | --------------------------------------- |
| **Image**  | `elasticsearch:8.13.0`                  |
| **Port**   | 9200                                    |
| **Config** | `infra/elasticsearch/elasticsearch.yml` |
| **Search** | `configs/hybrid-search.yaml`            |

**Elasticsearch** provides keyword-based (BM25) search capabilities that complement ChromaDB's vector similarity search, enabling a hybrid retrieval strategy that significantly improves RAG accuracy.

**Why Hybrid Search?**

- **Vector search alone misses exact matches** — If a user asks "What is the TLS 1.3 cipher suite configuration?", vector embeddings capture semantic meaning but may miss the exact acronym "TLS 1.3". Keyword search finds it precisely.
- **Keyword search alone misses semantic meaning** — If a user asks "How do I secure network connections?", keyword search won't find documents about "TLS" or "encryption" unless those exact words appear. Vector search understands the semantic relationship.
- **Hybrid = best of both** — Combining both retrieval methods with Reciprocal Rank Fusion (RRF) produces results that are both semantically relevant and keyword-accurate.

**Hybrid Search Pipeline:**

1. User query arrives at the Vector Service.
2. **Parallel retrieval:** ChromaDB returns top-20 by cosine similarity; Elasticsearch returns top-20 by BM25.
3. **RRF Fusion** — Results are merged using RRF with `k=60`, weighting vector results at 0.6 and keyword results at 0.4.
4. **Cross-Encoder Reranking** — The fused top-30 are reranked by a cross-encoder (`ms-marco-MiniLM-L-6-v2`) for final precision.
5. Top-10 results with scores are returned to the AI Service for RAG prompt construction.

**Elasticsearch Configuration:**

- Single-node cluster for development (no security, no replication).
- Custom analyzer with English stemmer, stop words, and lowercase normalization.
- In production, replaced with AWS OpenSearch (managed, multi-AZ, encryption at rest).

---

### 12. Model Gateway — LLM Routing / Factory Pattern

| Property   | Value                                        |
| ---------- | -------------------------------------------- |
| **Config** | `configs/model-gateway.yaml`                 |
| **Proto**  | `proto/gateway/v1/ModelGatewayService.proto` |

The **Model Gateway** is a configuration-driven LLM router that abstracts away provider-specific APIs behind a unified interface, with intelligent fallback, cost controls, and circuit breaking.

**Key Features:**

- **Fallback Chains** — Three pre-configured chains that the API Gateway selects based on request parameters:
  - `default` — `gpt-4o` → `claude-3-5-sonnet` → `gemini-1.5-pro` (best quality, falls back on failure).
  - `fast` — `gpt-4o-mini` → `claude-3-haiku` → `gemini-1.5-flash` (lowest latency).
  - `reasoning` — `o1` → `claude-3-5-sonnet` (complex reasoning tasks).

- **Priority-Based Routing** — Within each chain, providers are ordered by priority (1 = highest). If the primary provider fails or hits rate limits, the gateway automatically routes to the next provider in the chain.

- **Circuit Breaker** — If a provider returns 5 consecutive errors within a 30-second window, the circuit "opens" and all requests are immediately routed to the next provider. After a 60-second recovery period, the circuit "half-opens" and sends a single test request. If it succeeds, the circuit closes and normal routing resumes.

- **Cost Controls:**
  - **Daily budget** — $100/day default. When reached, requests are rejected with a 429 status.
  - **Per-request cap** — $5/request maximum. Prevents runaway costs from large context windows.
  - **Token tracking** — Every completion records input/output token counts and estimated cost.

- **Routing Rules** — Requests can be routed based on metadata (e.g., route all "code generation" requests to GPT-4o, route all "summarization" requests to the `fast` chain).

- **gRPC Contract** — The `ModelGatewayService.proto` defines RPCs for: `Complete`, `CompleteStream`, `Embed`, `GetUsageSummary`, `GetProviderStatus`, `GetRoutingConfig`, and `UpdateRoutingConfig`.

---

### 13. Unleash — Feature Flags

| Property   | Value                             |
| ---------- | --------------------------------- |
| **Image**  | `unleashorg/unleash-server:5.12`  |
| **Port**   | 4242                              |
| **URL**    | `https://unleash.nemo.local`      |
| **Config** | `infra/unleash/initial-flags.yml` |

**Unleash** is a feature flag management system that enables controlled rollouts, A/B testing, and instant feature kill-switches without code deployments.

**Initial Feature Flags (14 flags):**

| Flag                            | Type            | Default | Description                       |
| ------------------------------- | --------------- | ------- | --------------------------------- |
| `enable-openai`                 | Boolean         | ON      | Enable/disable OpenAI provider    |
| `enable-anthropic`              | Boolean         | ON      | Enable/disable Anthropic provider |
| `enable-google`                 | Boolean         | ON      | Enable/disable Google provider    |
| `enable-model-o1`               | Gradual Rollout | 10%     | o1 reasoning model (expensive)    |
| `enable-google-calendar-plugin` | Boolean         | ON      | Google Calendar integration       |
| `enable-slack-plugin`           | Boolean         | ON      | Slack integration                 |
| `enable-web-search-plugin`      | Boolean         | ON      | Web search plugin                 |
| `enable-research-agent`         | Boolean         | ON      | Multi-step research workflow      |
| `enable-task-execution-agent`   | Gradual Rollout | 25%     | Autonomous task execution         |
| `enable-hybrid-search`          | Boolean         | ON      | Hybrid vector+keyword search      |
| `enable-streaming-responses`    | Boolean         | ON      | Token-by-token streaming          |
| `enable-temporal-workflows`     | Boolean         | OFF     | Temporal durable workflows        |
| `enable-distributed-tracing`    | Boolean         | ON      | OTel distributed tracing          |
| `enable-vault-secrets`          | Boolean         | ON      | Vault secrets management          |

**How Services Use Flags:**

- Every service includes the Unleash client SDK.
- Before executing a feature path, the service checks the flag state: `if unleash.is_enabled("enable-hybrid-search"): use_hybrid() else: use_vector_only()`.
- Gradual rollout flags use consistent hashing by user ID — the same user always gets the same experience.
- Flags can be toggled in the Unleash UI instantly, taking effect within 10 seconds (polling interval).

---

### 14. Keycloak — Identity & Access Management

| Property   | Value                              |
| ---------- | ---------------------------------- |
| **Image**  | `quay.io/keycloak/keycloak:24.0`   |
| **Port**   | 8180 (dev), 8080 (internal)        |
| **URL**    | `https://auth.nemo.local`          |
| **Config** | `infra/keycloak/realm-export.json` |

**Keycloak** is a full-featured Identity and Access Management (IAM) server that provides OAuth2, OpenID Connect (OIDC), Single Sign-On (SSO), and Role-Based Access Control (RBAC) for the entire platform.

**Realm Configuration (`nemo`):**

- **Roles:**
  - `nemo-admin` — Full platform access: manage users, plugins, workflows, models, and system settings.
  - `nemo-user` — Standard access: chat, upload documents, run workflows, use plugins.
  - `nemo-viewer` — Read-only access: view chat history, browse documents, view workflow results.

- **OAuth2 Clients:**
  - `nemo-frontend` (Public client) — Used by the Next.js frontend for browser-based OIDC login. Redirect URIs: `https://nemo.local/*`. PKCE enabled for security.
  - `nemo-api` (Confidential client) — Used by the API Gateway for service-to-service token validation and token exchange. Client secret stored in Vault.

- **Seeded Users (Development):**
  - `admin` / `admin123` — Has `nemo-admin` role.
  - `user` / `user123` — Has `nemo-user` role.

- **OIDC Scopes:**
  - `openid` — Standard OIDC identity.
  - `profile` — User's name and avatar.
  - `email` — User's email address.
  - `nemo-roles` — Custom scope that includes a `realm_access.roles` claim in the JWT, enabling the API Gateway to extract roles for RBAC.

- **Security Features:**
  - Brute force protection: account locks after 5 failed login attempts.
  - Token lifetimes: access token = 5 minutes, refresh token = 30 minutes.
  - CORS allowed origins: `https://nemo.local`.

**Authentication Flow:**

1. User visits `https://nemo.local` → Frontend redirects to `https://auth.nemo.local/realms/nemo/protocol/openid-connect/auth`.
2. User logs in → Keycloak redirects back with an authorization code.
3. Frontend exchanges the code for tokens (access + refresh + ID token).
4. Frontend sends the access token as `Authorization: Bearer <token>` on every API request.
5. API Gateway validates the JWT signature against Keycloak's public key, extracts roles, enforces RBAC.

---

## Data Stores

### 15. PostgreSQL 16

| Property  | Value                |
| --------- | -------------------- |
| **Image** | `postgres:16-alpine` |
| **Port**  | 5432                 |

The primary relational database for all structured data. Stores user accounts, conversation history, plugin metadata, workflow definitions and state, document metadata, and Temporal's internal state. Initialized with migrations from `migrations/init.sql` that create the schema with proper indexes, foreign keys, and JSONB columns for flexible metadata storage.

---

### 16. Redis 7

| Property  | Value                       |
| --------- | --------------------------- |
| **Image** | `redis:7-alpine`            |
| **Port**  | 6379 (internal), 6380 (dev) |

In-memory data store used for: session caching (API Gateway sessions), rate limiting counters (distributed token bucket), LLM response caching (cache identical prompts to avoid redundant API calls), and pub/sub for real-time WebSocket event distribution. Password-protected with configurable credentials.

---

### 17. ChromaDB

| Property  | Value                       |
| --------- | --------------------------- |
| **Image** | `chromadb/chroma:0.5.3`     |
| **Port**  | 8000 (internal), 8005 (dev) |

Open-source vector database for semantic similarity search. Stores document chunk embeddings with metadata. Supports cosine, L2, and inner product distance metrics. Used as the primary vector store in the hybrid search pipeline, returning the top-k semantically similar chunks for any query embedding. Persistent storage backed by a Docker volume.

---

## Observability Stack

### 18. Prometheus

| Property   | Value                             |
| ---------- | --------------------------------- |
| **Image**  | `prom/prometheus:latest`          |
| **Port**   | 9090 (internal), 9093 (dev)       |
| **URL**    | `https://prometheus.nemo.local`   |
| **Config** | `infra/prometheus/prometheus.yml` |

Time-series metrics database that scrapes all services every 10-15 seconds. **14 scrape targets:** API Gateway, AI Service, Plugin Service, Workflow Service, Vector Service, Traefik, Prometheus self, Temporal, Tempo, OTel Collector, Keycloak, Unleash, Elasticsearch, and Vault. Enables remote-write receiver for the OTel Collector to push metrics. Stores 30 days of data with exemplar storage enabled for trace-metric correlation.

---

### 19. Grafana

| Property  | Value                        |
| --------- | ---------------------------- |
| **Image** | `grafana/grafana:latest`     |
| **Port**  | 3000 (internal), 3001 (dev)  |
| **URL**   | `https://grafana.nemo.local` |

Visualization and dashboarding platform with three auto-provisioned datasources:

- **Prometheus** (uid: `prometheus`) — Metrics queries.
- **Loki** (uid: `loki`) — Log queries with derived fields linking to trace IDs.
- **Tempo** (uid: `tempo`) — Trace queries with trace-to-logs and trace-to-metrics correlation.

**Three auto-provisioned dashboards:**

- **Nemo Overview** — Request rates, latencies, error rates, resource usage across all services.
- **Nemo Logs** — Centralized log viewer with service/level filtering and live tail.
- **Nemo Distributed Tracing** — Service map, trace search, p50/p95/p99 latencies, OTel Collector health.

---

### 20. Loki + Promtail

| Property     | Value                            |
| ------------ | -------------------------------- |
| **Loki**     | `grafana/loki:latest`            |
| **Promtail** | `grafana/promtail:latest`        |
| **Config**   | `infra/loki/`, `infra/promtail/` |

**Loki** is a log aggregation system (like Prometheus, but for logs). **Promtail** is its agent that tails Docker container logs and ships them to Loki with labels (container_name, service). Supports LogQL queries in Grafana for structured log exploration. Loki's derived fields configuration automatically links log entries containing `trace_id` to the corresponding Tempo trace.

---

## Networking & Security

### 21. Traefik — Reverse Proxy / TLS Termination

| Property   | Value                                             |
| ---------- | ------------------------------------------------- |
| **Image**  | `traefik:latest`                                  |
| **Ports**  | 80, 443 (HTTPS), 9090 (gRPC)                      |
| **URL**    | `https://traefik.nemo.local`                      |
| **Config** | `infra/proxy/traefik.yml`, `infra/proxy/dynamic/` |

**Traefik** serves as the edge reverse proxy handling all inbound traffic with:

- **TLS 1.2/1.3 Termination** — All traffic is encrypted. HTTP (port 80) automatically redirects to HTTPS (port 443) with a 308 Permanent Redirect. Development uses mkcert-generated certificates; production uses Let's Encrypt with ACME auto-renewal.
- **9 TLS-covered domains:** `nemo.local`, `api.nemo.local`, `grafana.nemo.local`, `prometheus.nemo.local`, `traefik.nemo.local`, `auth.nemo.local`, `vault.nemo.local`, `temporal.nemo.local`, `unleash.nemo.local`.
- **Security Middlewares:** Strict security headers (HSTS, X-Frame-Options, CSP), CORS with explicit allowed origins/methods/headers, Gzip compression, request size limiting (50MB max body), and rate limiting.
- **Three Docker Networks:**
  - `nemo-frontend` (bridge) — Traefik ↔ Frontend ↔ Keycloak.
  - `nemo-backend` (internal) — API Gateway ↔ Backend services.
  - `nemo-infra` (internal) — All infrastructure services (databases, Kafka, observability).
- **Docker API** integration for automatic service discovery via container labels.

---

## gRPC / Protobuf Contracts

All inter-service communication uses gRPC with Protocol Buffer definitions:

| Proto File                                   | Service          | RPCs                                                                |
| -------------------------------------------- | ---------------- | ------------------------------------------------------------------- |
| `proto/ai/v1/AiService.proto`                | AI Service       | Chat, StreamChat, GetConversation                                   |
| `proto/plugin/v1/PluginService.proto`        | Plugin Service   | ExecutePlugin, ListPlugins, GetPlugin                               |
| `proto/workflow/v1/WorkflowService.proto`    | Workflow Service | StartWorkflow, GetWorkflowStatus, CancelWorkflow                    |
| `proto/vector/v1/VectorService.proto`        | Vector Service   | Search, Ingest, DeleteDocument                                      |
| `proto/gateway/v1/ModelGatewayService.proto` | Model Gateway    | Complete, CompleteStream, Embed, GetUsageSummary, GetProviderStatus |
| `proto/search/v1/HybridSearchService.proto`  | Hybrid Search    | Search, IndexDocument, DeleteDocument, GetIndexStats                |

---

## Infrastructure as Code — Terraform

| Property     | Value                           |
| ------------ | ------------------------------- |
| **Location** | `terraform/`                    |
| **Backend**  | S3 (state) + DynamoDB (locking) |
| **Provider** | AWS                             |

Complete AWS infrastructure provisioning via **7 Terraform modules:**

| Module        | Description                                                                                                          | Key Resources                  |
| ------------- | -------------------------------------------------------------------------------------------------------------------- | ------------------------------ |
| `networking`  | VPC with public/private subnets across 3 AZs, NAT Gateway, Internet Gateway, route tables                            | VPC, 6 subnets, NAT GW, IGW    |
| `eks`         | Managed Kubernetes cluster with auto-scaling node groups and OIDC provider for IAM Roles for Service Accounts (IRSA) | EKS cluster, node group, OIDC  |
| `rds`         | PostgreSQL 16 with gp3 storage, encryption at rest, performance insights, automated backups                          | RDS instance, subnet group, SG |
| `elasticache` | Redis 7.1 replication group with encryption in transit and at rest, automatic failover                               | ElastiCache cluster, SG        |
| `msk`         | Kafka 3.6.0 managed streaming with TLS encryption and EBS storage                                                    | MSK cluster, SG                |
| `opensearch`  | OpenSearch 2.13 (managed Elasticsearch) with zone awareness, EBS storage, master nodes                               | OpenSearch domain, SG          |
| `monitoring`  | CloudWatch log groups for all services + CPU/memory alarms                                                           | Log groups, alarms             |

**Two environment configurations:**

- `environments/dev.tfvars` — Smaller instances (t4g.medium nodes, db.t4g.medium RDS, cache.t3.medium Redis).
- `environments/prod.tfvars` — Production sizing (m5.xlarge nodes, db.r6g.xlarge RDS, cache.r6g.large Redis, 3 brokers, 3 master + 3 data OpenSearch nodes).

---

## Kubernetes Deployment

| Property     | Value     |
| ------------ | --------- |
| **Location** | `k8s/`    |
| **Tool**     | Kustomize |

Production-ready Kubernetes manifests with Kustomize overlay pattern:

**Base (`k8s/base/`):**

- **3 Namespaces:** `nemo` (application), `nemo-infra` (infrastructure), `nemo-monitoring` (observability).
- **6 Deployments:** api-gateway, ai-service, plugin-service, workflow-service, vector-service, frontend — each with configurable replicas, resource limits, readiness/liveness probes, and environment variables sourced from ConfigMaps and Secrets.
- **6 Services:** ClusterIP services exposing each deployment's ports.
- **6 HorizontalPodAutoscalers:** CPU and memory-based auto-scaling with configurable min/max replicas.
- **6 PodDisruptionBudgets:** Ensures minimum availability during rolling updates and node drains.
- **6 ServiceAccounts:** Per-service accounts for IRSA (IAM Roles for Service Accounts) in EKS.
- **NetworkPolicies:** Default deny ingress in the `nemo` namespace, with explicit allow rules for intra-namespace traffic, ingress controller traffic, and monitoring scraping.
- **Ingress:** NGINX Ingress with TLS termination, CORS, cert-manager integration. Separate HTTP and gRPC ingress resources.
- **ConfigMaps:** Infrastructure endpoints (Kafka brokers, Elasticsearch URL, Vault address, etc.).
- **Secrets:** Templates for database credentials, Redis credentials, LLM API keys, and OAuth credentials — annotated for Vault Agent injection.

**Overlays:**

- `k8s/overlays/dev/` — Single replicas, reduced resources (100m CPU / 128Mi memory), disabled HPA max, self-signed TLS, `dev` image tags.
- `k8s/overlays/staging/` — Base replicas (2), capped HPA max (4), `staging` image tags.
- `k8s/overlays/prod/` — Increased replicas (3 for critical services), production resource limits (up to 4 CPU / 2Gi for AI Service), higher HPA limits (up to 20 for API Gateway), PDB minAvailable=2, production domain names, SHA-based image tags set by CI/CD.

---

## Argo CD — GitOps Continuous Delivery

| Property     | Value         |
| ------------ | ------------- |
| **Location** | `k8s/argocd/` |

**Argo CD** watches the Git repository and automatically synchronizes Kubernetes cluster state with the desired state defined in the `k8s/` manifests.

**Configuration:**

- **AppProject (`nemo`)** — Scoped to the Nemo repo and three namespaces. Two roles: `admin` (full access) and `developer` (read + sync).
- **Three Applications:**
  - `nemo-apps-dev` — Watches `develop` branch, `k8s/overlays/dev/`. **Auto-sync with prune and self-heal** — any manual cluster changes are automatically reverted.
  - `nemo-apps-staging` — Watches `staging` branch, `k8s/overlays/staging/`. Auto-sync with prune.
  - `nemo-apps-prod` — Watches `main` branch, `k8s/overlays/prod/`. **Manual sync only** — requires explicit approval before deploying to production.
- **Notifications** — Configured triggers for sync-succeeded, sync-failed, health-degraded, and deployed events.

**Deployment Flow:**

1. Developer pushes code → CI builds container images → CI updates image tags in `k8s/overlays/prod/kustomization.yaml`.
2. Argo CD detects the manifest change → shows "OutOfSync" in the UI.
3. For dev/staging: automatic sync. For production: requires manual "Sync" click by an admin.
4. Argo CD applies the changes via `kubectl apply` with progressive rollout — monitoring health between steps.

---

## CI/CD Pipelines

| Location | `/.github/workflows/` |
| -------- | --------------------- |

**7 GitHub Actions workflows:**

| Workflow            | Trigger                         | Description                                                                                                                                         |
| ------------------- | ------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ci-gateway.yml`    | Push to `services/api-gateway/` | Go lint (golangci-lint), test, build                                                                                                                |
| `ci-python.yml`     | Push to `services/*-service/`   | Python lint (ruff), type check (mypy), test (pytest), coverage                                                                                      |
| `ci-frontend.yml`   | Push to `services/frontend/`    | Node lint (ESLint), type check, build, Lighthouse audit                                                                                             |
| `ci-docker.yml`     | Push to any `Dockerfile`        | Build all Docker images, verify compose validity                                                                                                    |
| `ci-terraform.yml`  | Push to `terraform/`            | Terraform fmt, validate, TFLint, tfsec security scan, plan preview on PRs                                                                           |
| `ci-kubernetes.yml` | Push to `k8s/` or `proto/`      | Kustomize build validation (all overlays), kubeconform schema validation, Protobuf lint (buf), Trivy security scan                                  |
| `cd-deploy.yml`     | Push to `main`                  | Build + push all 6 container images to GHCR, Trivy vulnerability scan, update Kustomize image tags, commit manifest changes (triggers Argo CD sync) |

---

## Configuration Files

| File                         | Description                                                             |
| ---------------------------- | ----------------------------------------------------------------------- |
| `configs/gateway.yaml`       | API Gateway routing rules, timeout settings, CORS configuration         |
| `configs/models.yaml`        | LLM provider definitions (endpoints, model names, pricing)              |
| `configs/plugins.yaml`       | Plugin registry: names, schemas, capability tags, timeouts              |
| `configs/workflows.yaml`     | Workflow definitions: steps, conditions, parallelism settings           |
| `configs/model-gateway.yaml` | LLM routing rules, fallback chains, circuit breaker, cost controls      |
| `configs/hybrid-search.yaml` | Search pipeline: vector/keyword weights, RRF parameters, reranker model |
| `events/schemas.yaml`        | Kafka event schemas: topic names, payload structures, versioning        |

---

## Quick Start

```bash
# 1. Clone
git clone https://github.com/jagadeeshm007/nemo.git
cd nemo

# 2. Copy environment config
cp .env.dev .env

# 3. Start all services (24 containers)
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml up -d

# 4. Verify everything is healthy
docker compose -f docker-compose.base.yml -f docker-compose.dev.yml ps

# 5. Initialize Vault secrets (first run only)
docker exec -it nemo-vault sh /vault/scripts/init-dev.sh

# 6. Generate protobuf files
make proto

# 7. Run all tests
make test
```

---

## Endpoints

| Service           | URL                             | Credentials          |
| ----------------- | ------------------------------- | -------------------- |
| Frontend          | `https://nemo.local`            | Login via Keycloak   |
| API Gateway       | `https://api.nemo.local`        | Bearer token         |
| Keycloak (IAM)    | `https://auth.nemo.local`       | admin / admin        |
| Grafana           | `https://grafana.nemo.local`    | admin / admin        |
| Prometheus        | `https://prometheus.nemo.local` | —                    |
| Traefik Dashboard | `https://traefik.nemo.local`    | —                    |
| Temporal UI       | `https://temporal.nemo.local`   | —                    |
| Vault UI          | `https://vault.nemo.local`      | Root token from init |
| Unleash           | `https://unleash.nemo.local`    | Admin API token      |

---

## License

Proprietary — All rights reserved.
