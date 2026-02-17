# SaaS Plan (v1) — bnb-rag-bot → Plug-and-Play B2B

Owner decisions (Rafa):
- **Tenant = Company**
- **Workspace** is an internal subdivision under a tenant (not separately billed)
- **User model v1:** 1 user = 1 tenant (no multi-tenant membership)

## Milestones (execution order)

### Milestone 1 — Auth + Tenant + RLS
**Goal:** foundation-grade security + isolation.

Deliverables:
- Auth: register/login + **refresh token rotation**, logout/revoke
- Email verification
- Reset password
- RBAC: Platform Admin / Company Admin / Company User
- Postgres multi-tenant: `tenant_id` mandatory on all tenant-scoped tables
- **RLS enabled** + policies (tenant isolation)
- DB middleware: `SET LOCAL app.tenant_id` for each request/tx
- Tests: auth + RLS isolation smoke tests

### Milestone 2 — Billing + Usage + Redis + Worker
- Stripe plans + subscription table + webhooks
- Redis hard-check limits + async usage events → worker → batch consolidate
- Rate limiting per tenant via Redis

### Milestone 3 — Agent CRUD + Vector Namespace
- agent model + namespace per `agent_id`

### Milestone 4 — Async Ingest Pipeline
- upload → store → queue → worker pipeline (extract/chunk/embed/index) + status + DLQ

### Milestone 5 — Telegram + Logs
- token setup + webhook receiver + retry + conversation logs
- channel abstraction interface

### Milestone 6 — Frontend
- Next.js premium UI (after Milestone 1 done)

### Milestone 7 — WhatsApp + Widget

## Data model (v1 sketch)

### tenants
- `id`, `company_name`, `plan`, ...

### platform_users
- `id`, `tenant_id`, `email`, `password_hash`, `role`, `email_verified_at`, ...

### refresh_tokens
- `id`, `tenant_id`, `user_id`, `token_hash`, `expires_at`, `revoked_at`, `created_at`

### password_resets / email_verifications
- `tenant_id`, `user_id`, `token_hash`, `expires_at`, `used_at`

### workspaces (internal)
- `id`, `tenant_id`, `name`, ...

## RLS approach
- Tenant-scoped tables get: `ALTER TABLE ... ENABLE ROW LEVEL SECURITY;`
- Policy example:
  - `USING (tenant_id = current_setting('app.tenant_id')::uuid)`
  - `WITH CHECK (tenant_id = current_setting('app.tenant_id')::uuid)`
- API sets `SET LOCAL app.tenant_id = '<uuid>'` at tx start.

Notes:
- Keep a clear separation between API and worker processes.
- Avoid synchronous heavy operations in API.
- Structured logs everywhere.
