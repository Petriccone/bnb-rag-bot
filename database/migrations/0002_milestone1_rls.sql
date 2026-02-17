-- Milestone 1 - RLS enforcement (v1)
-- Requires app to set: SET LOCAL app.tenant_id = '<uuid>'
-- Optional: SET LOCAL app.user_id, app.role

BEGIN;

-- Helper: current tenant
CREATE OR REPLACE FUNCTION app_current_tenant_id() RETURNS uuid
LANGUAGE sql STABLE AS $$
  SELECT NULLIF(current_setting('app.tenant_id', true), '')::uuid;
$$;

-- Enable RLS + tenant isolation policy macro
-- Tenant-scoped tables list (extend as you add tables)
DO $$
DECLARE
  t text;
  tables text[] := ARRAY[
    'agents',
    'conversations',
    'tenant_conversation_log',
    'leads',
    'documents',
    'platform_users',
    'tenant_whatsapp_config',
    'tenant_evolution_config',
    'tenant_telegram_config',
    'refresh_tokens',
    'email_verification_tokens',
    'password_reset_tokens',
    'workspaces'
  ];
BEGIN
  FOREACH t IN ARRAY tables LOOP
    EXECUTE format('ALTER TABLE IF EXISTS %I ENABLE ROW LEVEL SECURITY', t);
    EXECUTE format('ALTER TABLE IF EXISTS %I FORCE ROW LEVEL SECURITY', t);

    -- Drop old policy if exists (so re-run is safe-ish)
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I', t);

    EXECUTE format(
      'CREATE POLICY tenant_isolation ON %I '
      'USING (tenant_id = app_current_tenant_id()) '
      'WITH CHECK (tenant_id = app_current_tenant_id())',
      t
    );
  END LOOP;
END $$;

-- tenants table: special case.
-- In v1 (1 user = 1 tenant), tenant row is visible only when app.tenant_id matches.
ALTER TABLE IF EXISTS tenants ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tenants FORCE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS tenant_self ON tenants;
CREATE POLICY tenant_self ON tenants
  USING (id = app_current_tenant_id())
  WITH CHECK (id = app_current_tenant_id());

COMMIT;
