-- Milestone 1 - Auth/RBAC foundation (v1)
-- Safe to run multiple times where possible.

BEGIN;

-- Extensions (Supabase usually has pgcrypto)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- platform_users: RBAC + email verification
ALTER TABLE IF EXISTS platform_users
  ADD COLUMN IF NOT EXISTS role TEXT NOT NULL DEFAULT 'company_admin',
  ADD COLUMN IF NOT EXISTS email_verified_at TIMESTAMPTZ,
  ADD COLUMN IF NOT EXISTS disabled_at TIMESTAMPTZ;

-- restrict role values
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'platform_users_role_check'
  ) THEN
    ALTER TABLE platform_users
      ADD CONSTRAINT platform_users_role_check
      CHECK (role IN ('platform_admin','company_admin','company_user'));
  END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_platform_users_tenant_role ON platform_users (tenant_id, role);

-- Refresh tokens (hashed)
CREATE TABLE IF NOT EXISTS refresh_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES platform_users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  revoked_at TIMESTAMPTZ,
  replaced_by UUID,
  user_agent TEXT,
  ip INET,
  UNIQUE (token_hash)
);

CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_active
  ON refresh_tokens (tenant_id, user_id, revoked_at, expires_at);

-- Email verification tokens (hashed)
CREATE TABLE IF NOT EXISTS email_verification_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES platform_users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  UNIQUE (token_hash)
);

CREATE INDEX IF NOT EXISTS idx_email_verif_user_active
  ON email_verification_tokens (tenant_id, user_id, used_at, expires_at);

-- Password reset tokens (hashed)
CREATE TABLE IF NOT EXISTS password_reset_tokens (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  user_id UUID NOT NULL REFERENCES platform_users(id) ON DELETE CASCADE,
  token_hash TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  used_at TIMESTAMPTZ,
  UNIQUE (token_hash)
);

CREATE INDEX IF NOT EXISTS idx_pwd_reset_user_active
  ON password_reset_tokens (tenant_id, user_id, used_at, expires_at);

-- Workspaces (internal subdivisions under tenant; not billed separately)
CREATE TABLE IF NOT EXISTS workspaces (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  UNIQUE (tenant_id, name)
);

CREATE INDEX IF NOT EXISTS idx_workspaces_tenant ON workspaces (tenant_id);

COMMIT;
