-- Usage tracking: tokens, mensagens, storage por tenant.
-- Usado para billing e limites de plano.

-- Histórico de uso mensal por tenant
CREATE TABLE IF NOT EXISTS tenant_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    year_month TEXT NOT NULL, -- formato: YYYY-MM
    tokens_used INTEGER NOT NULL DEFAULT 0,
    tokens_limit INTEGER NOT NULL DEFAULT 0,
    messages_sent INTEGER NOT NULL DEFAULT 0,
    messages_limit INTEGER NOT NULL DEFAULT 0,
    storage_mb REAL NOT NULL DEFAULT 0,
    storage_limit_mb REAL NOT NULL DEFAULT 0,
    documents_count INTEGER NOT NULL DEFAULT 0,
    documents_limit INTEGER NOT NULL DEFAULT 0,
    agents_count INTEGER NOT NULL DEFAULT 0,
    agents_limit INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, year_month)
);

CREATE INDEX IF NOT EXISTS idx_tenant_usage_tenant_month ON tenant_usage (tenant_id, year_month);

-- Log detalhado de usage (opcional, para debugging)
CREATE TABLE IF NOT EXISTS tenant_usage_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    user_id UUID REFERENCES platform_users(id) ON DELETE SET NULL,
    event_type TEXT NOT NULL, -- message_sent, token_used, document_uploaded, document_deleted
    tokens INTEGER NOT NULL DEFAULT 0,
    storage_bytes BIGINT NOT NULL DEFAULT 0,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_usage_log_tenant ON tenant_usage_log (tenant_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_tenant_usage_log_type ON tenant_usage_log (event_type, created_at DESC);

-- Planos e seus limites
-- free: 2000 msgs/mês, 100K tokens/mês, 50MB storage, 3 agents, 10 docs
-- pro: 10000 msgs/mês, 500K tokens/mês, 500MB storage, 10 agents, 50 docs
-- enterprise: ilimitado (0 = ilimitado)

-- Limites de plano (reference)
-- CREATE TYPE plan_tier AS ENUM ('free', 'pro', 'enterprise');
