-- Schema multi-tenant para a plataforma SaaS.
-- Execute no Postgres/Supabase após o schema legado (execution/supabase_schema.sql).
-- Isolamento total por tenant_id; nenhum dado compartilhado entre tenants.

CREATE TABLE IF NOT EXISTS tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    plan TEXT NOT NULL DEFAULT 'free' CHECK (plan IN ('free', 'pro', 'enterprise')),
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenants_plan ON tenants (plan);

CREATE TABLE IF NOT EXISTS agents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    niche TEXT,
    prompt_custom TEXT,
    active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_agents_tenant ON agents (tenant_id);
CREATE INDEX IF NOT EXISTS idx_agents_tenant_active ON agents (tenant_id, active);

CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    lead_id TEXT NOT NULL,
    state TEXT NOT NULL DEFAULT 'descoberta',
    spin_answers JSONB DEFAULT '{}',
    lead_classification TEXT NOT NULL DEFAULT 'frio',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, agent_id, lead_id)
);

CREATE INDEX IF NOT EXISTS idx_conversations_tenant_agent ON conversations (tenant_id, agent_id);
CREATE INDEX IF NOT EXISTS idx_conversations_tenant_lead ON conversations (tenant_id, lead_id);

-- Log de mensagens por tenant (legado usa conversation_log sem tenant_id)
CREATE TABLE IF NOT EXISTS tenant_conversation_log (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    lead_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content_type TEXT NOT NULL DEFAULT 'text',
    content TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_conversation_log_lead_ts ON tenant_conversation_log (tenant_id, lead_id, timestamp DESC);

CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    lead_id TEXT NOT NULL,
    classification TEXT NOT NULL DEFAULT 'frio' CHECK (classification IN ('frio', 'morno', 'quente', 'cliente')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (tenant_id, lead_id)
);

CREATE INDEX IF NOT EXISTS idx_leads_tenant ON leads (tenant_id);

CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    embedding_namespace TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_tenant ON documents (tenant_id);
CREATE INDEX IF NOT EXISTS idx_documents_namespace ON documents (tenant_id, embedding_namespace);

-- Usuários da plataforma (login JWT). Um usuário pertence a um tenant.
CREATE TABLE IF NOT EXISTS platform_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES tenants(id) ON DELETE CASCADE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_platform_users_tenant ON platform_users (tenant_id);
CREATE INDEX IF NOT EXISTS idx_platform_users_email ON platform_users (email);

-- WhatsApp Cloud API: um tenant pode conectar um número (phone_number_id + token).
CREATE TABLE IF NOT EXISTS tenant_whatsapp_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE UNIQUE,
    phone_number_id TEXT NOT NULL,
    access_token_encrypted TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_whatsapp_phone ON tenant_whatsapp_config (phone_number_id);

-- Evolution API: conexão por QR (um tenant = uma instância).
CREATE TABLE IF NOT EXISTS tenant_evolution_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE UNIQUE,
    base_url TEXT NOT NULL,
    api_key_encrypted TEXT NOT NULL,
    instance_name TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_evolution_instance ON tenant_evolution_config (instance_name);

-- Telegram: cada tenant cola o token do bot no dashboard; webhook recebe e responde.
CREATE TABLE IF NOT EXISTS tenant_telegram_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE UNIQUE,
    bot_token_encrypted TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
