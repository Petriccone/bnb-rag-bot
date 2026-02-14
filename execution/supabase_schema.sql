-- Execute este SQL no Supabase: SQL Editor -> New query -> Cole e rode.
-- Cria as tabelas usadas pelo bot SDR (sessions e conversation_log).

CREATE TABLE IF NOT EXISTS sessions (
  user_id TEXT PRIMARY KEY,
  current_state TEXT NOT NULL DEFAULT 'descoberta',
  lead_classification TEXT NOT NULL DEFAULT 'frio',
  spin_answers JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS conversation_log (
  id BIGSERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  role TEXT NOT NULL,
  content_type TEXT NOT NULL DEFAULT 'text',
  content TEXT NOT NULL,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_conversation_log_user_ts
  ON conversation_log (user_id, timestamp DESC);

-- Opcional: RLS. Se usar service_role key no bot, o acesso já bypassa RLS.
-- Para restringir por usuário autenticado (ex.: dashboard), descomente e ajuste:
-- ALTER TABLE sessions ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE conversation_log ENABLE ROW LEVEL SECURITY;
