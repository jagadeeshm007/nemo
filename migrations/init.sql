-- =============================================================================
-- Nemo Platform — Database Schema (PostgreSQL)
-- =============================================================================
-- This file is mounted into the postgres container via docker-compose.yml
-- and runs automatically on first startup.
-- =============================================================================

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- Users & Authentication
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   TEXT NOT NULL,
    display_name    VARCHAR(255) NOT NULL DEFAULT '',
    role            VARCHAR(50) NOT NULL DEFAULT 'user',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);

-- =============================================================================
-- Conversations & Messages
-- =============================================================================

CREATE TABLE IF NOT EXISTS conversations (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title           VARCHAR(500) NOT NULL DEFAULT 'New Conversation',
    model           VARCHAR(100) NOT NULL DEFAULT 'gpt-4o',
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_updated ON conversations(updated_at DESC);

CREATE TABLE IF NOT EXISTS messages (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content         TEXT NOT NULL,
    model           VARCHAR(100),
    token_count     INTEGER DEFAULT 0,
    tool_calls      JSONB,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at);

-- =============================================================================
-- Models Configuration
-- =============================================================================

CREATE TABLE IF NOT EXISTS model_configs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    provider        VARCHAR(50) NOT NULL,
    model_id        VARCHAR(100) NOT NULL UNIQUE,
    display_name    VARCHAR(255) NOT NULL,
    context_window  INTEGER NOT NULL DEFAULT 4096,
    max_output      INTEGER NOT NULL DEFAULT 4096,
    capabilities    JSONB NOT NULL DEFAULT '[]',
    cost_per_1k_input   DECIMAL(10, 6) DEFAULT 0,
    cost_per_1k_output  DECIMAL(10, 6) DEFAULT 0,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    config          JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_model_configs_provider ON model_configs(provider);

-- =============================================================================
-- Plugins
-- =============================================================================

CREATE TABLE IF NOT EXISTS plugins (
    id              VARCHAR(100) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    description     TEXT DEFAULT '',
    version         VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    category        VARCHAR(100) DEFAULT 'general',
    state           VARCHAR(20) NOT NULL DEFAULT 'registered'
                    CHECK (state IN ('registered', 'active', 'inactive', 'error')),
    auth_type       VARCHAR(50) DEFAULT 'none',
    base_url        TEXT,
    config          JSONB NOT NULL DEFAULT '{}',
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS plugin_actions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    plugin_id       VARCHAR(100) NOT NULL REFERENCES plugins(id) ON DELETE CASCADE,
    name            VARCHAR(100) NOT NULL,
    description     TEXT DEFAULT '',
    input_schema    JSONB NOT NULL DEFAULT '{}',
    output_schema   JSONB NOT NULL DEFAULT '{}',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_plugin_actions_plugin ON plugin_actions(plugin_id);
CREATE UNIQUE INDEX idx_plugin_actions_unique ON plugin_actions(plugin_id, name);

-- =============================================================================
-- Workflows
-- =============================================================================

CREATE TABLE IF NOT EXISTS workflows (
    id              VARCHAR(100) PRIMARY KEY,
    name            VARCHAR(255) NOT NULL,
    description     TEXT DEFAULT '',
    version         VARCHAR(50) NOT NULL DEFAULT '1.0.0',
    steps           JSONB NOT NULL DEFAULT '[]',
    input_schema    JSONB NOT NULL DEFAULT '{}',
    output_mapping  JSONB NOT NULL DEFAULT '{}',
    tags            JSONB NOT NULL DEFAULT '[]',
    max_retries     INTEGER DEFAULT 2,
    timeout_seconds INTEGER DEFAULT 600,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS workflow_runs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_id     VARCHAR(100) NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'waiting')),
    input_data      JSONB NOT NULL DEFAULT '{}',
    output_data     JSONB,
    error           TEXT,
    context         JSONB NOT NULL DEFAULT '{}',
    created_by      UUID REFERENCES users(id),
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_workflow_runs_workflow ON workflow_runs(workflow_id);
CREATE INDEX idx_workflow_runs_status ON workflow_runs(status);
CREATE INDEX idx_workflow_runs_created ON workflow_runs(created_at DESC);

CREATE TABLE IF NOT EXISTS workflow_step_results (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    run_id          UUID NOT NULL REFERENCES workflow_runs(id) ON DELETE CASCADE,
    step_id         VARCHAR(100) NOT NULL,
    status          VARCHAR(20) NOT NULL DEFAULT 'pending',
    output          JSONB,
    error           TEXT,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    duration_ms     DOUBLE PRECISION DEFAULT 0
);

CREATE INDEX idx_step_results_run ON workflow_step_results(run_id);

-- =============================================================================
-- Documents (Vector Service)
-- =============================================================================

CREATE TABLE IF NOT EXISTS documents (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    filename        VARCHAR(500) NOT NULL,
    content_hash    VARCHAR(64) NOT NULL,
    collection      VARCHAR(100) NOT NULL DEFAULT 'default',
    status          VARCHAR(20) NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'processing', 'indexed', 'failed')),
    chunk_count     INTEGER DEFAULT 0,
    file_size_bytes BIGINT DEFAULT 0,
    mime_type       VARCHAR(100) DEFAULT '',
    metadata        JSONB NOT NULL DEFAULT '{}',
    error           TEXT,
    uploaded_by     UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_documents_collection ON documents(collection);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_hash ON documents(content_hash);

-- =============================================================================
-- Audit Log
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(100) NOT NULL,
    resource_type   VARCHAR(100) NOT NULL,
    resource_id     VARCHAR(255),
    details         JSONB NOT NULL DEFAULT '{}',
    ip_address      INET,
    user_agent      TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);

-- =============================================================================
-- API Keys
-- =============================================================================

CREATE TABLE IF NOT EXISTS api_keys (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name            VARCHAR(255) NOT NULL,
    key_hash        VARCHAR(64) NOT NULL UNIQUE,
    key_prefix      VARCHAR(10) NOT NULL,
    scopes          JSONB NOT NULL DEFAULT '["read"]',
    is_active       BOOLEAN NOT NULL DEFAULT true,
    last_used_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_user ON api_keys(user_id);

-- =============================================================================
-- Usage Tracking
-- =============================================================================

CREATE TABLE IF NOT EXISTS usage_records (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID REFERENCES users(id),
    service         VARCHAR(50) NOT NULL,
    model           VARCHAR(100),
    prompt_tokens   INTEGER DEFAULT 0,
    completion_tokens INTEGER DEFAULT 0,
    total_tokens    INTEGER DEFAULT 0,
    cost_usd        DECIMAL(10, 6) DEFAULT 0,
    metadata        JSONB NOT NULL DEFAULT '{}',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_usage_user ON usage_records(user_id);
CREATE INDEX idx_usage_created ON usage_records(created_at DESC);
CREATE INDEX idx_usage_service ON usage_records(service);

-- =============================================================================
-- Seed: Default admin user (password: admin123)
-- =============================================================================

INSERT INTO users (email, password_hash, display_name, role)
VALUES (
    'admin@nemo.ai',
    crypt('admin123', gen_salt('bf')),
    'Admin',
    'admin'
) ON CONFLICT (email) DO NOTHING;
