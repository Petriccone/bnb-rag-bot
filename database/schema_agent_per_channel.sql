-- Permite escolher um agente por canal (Telegram, WhatsApp). Rode no Supabase após o schema principal.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tenant_telegram_config' AND column_name = 'agent_id') THEN
    ALTER TABLE tenant_telegram_config ADD COLUMN agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tenant_whatsapp_config' AND column_name = 'agent_id') THEN
    ALTER TABLE tenant_whatsapp_config ADD COLUMN agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;
  END IF;
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'tenant_evolution_config' AND column_name = 'agent_id') THEN
    ALTER TABLE tenant_evolution_config ADD COLUMN agent_id UUID REFERENCES agents(id) ON DELETE SET NULL;
  END IF;
END $$;

COMMENT ON COLUMN tenant_telegram_config.agent_id IS 'Agente usado neste bot Telegram; NULL = primeiro agente ativo do tenant.';
COMMENT ON COLUMN tenant_whatsapp_config.agent_id IS 'Agente usado nesta conta WhatsApp; NULL = primeiro agente ativo.';
COMMENT ON COLUMN tenant_evolution_config.agent_id IS 'Agente usado nesta instância Evolution (QR); NULL = primeiro agente ativo.';
