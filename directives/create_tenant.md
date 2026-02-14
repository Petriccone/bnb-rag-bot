# Criação de tenant (empresa)

## Objetivo
Cadastrar uma nova empresa (tenant) na plataforma SaaS com isolamento total de dados.

## Regras
- Todo tenant deve ter: `company_name`, `plan` (free/pro/enterprise).
- `plan` define limites (agentes, mensagens/mês). Ver billing_rules.md.
- Ao criar tenant, criar registro em `tenants` com id UUID.
- Não compartilhar dados entre tenants; todas as queries devem filtrar por `tenant_id`.

## Campos
- company_name (obrigatório)
- plan (default: free)
- settings (JSON opcional: drive_folder_id, etc.)

## Fluxo
1. Validar nome e plano.
2. Inserir em `tenants`.
3. Retornar id do tenant para uso em agentes e documentos.
