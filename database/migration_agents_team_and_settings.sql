-- Migration: Adicionar team_id e settings à tabela agents
-- Caso as colunas não existam (ex: em ambientes sem o router de teams inicializado)

ALTER TABLE agents ADD COLUMN IF NOT EXISTS team_id UUID REFERENCES agent_teams(id) ON DELETE SET NULL;
ALTER TABLE agents ADD COLUMN IF NOT EXISTS settings JSONB DEFAULT '{}'::jsonb;

COMMENT ON COLUMN agents.team_id IS 'ID da equipe (swarm) a qual o agente pertence.';
COMMENT ON COLUMN agents.settings IS 'Configurações extras do agente (ex: delegação, parâmetros LLM).';
