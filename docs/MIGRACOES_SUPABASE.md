# Migrações no Supabase – ordem de execução

Execute no **SQL Editor** do Supabase (Database → SQL Editor) na ordem abaixo. Pode colar e rodar um bloco por vez.

---

## 1. Schema principal (se ainda não rodou)

Arquivo: **`database/schema.sql`**

Cria tabelas: `tenants`, `agents`, `conversations`, `tenant_conversation_log`, `leads`, `documents`, `platform_users`, configs de WhatsApp/Evolution/Telegram.

---

## 2. Base de conhecimento (RAG com embeddings)

Arquivo: **`database/schema_pgvector.sql`**

- Habilita a extensão **vector**
- Cria a tabela **`document_chunks`** (chunks + embedding para busca semântica)

Necessário para: upload de documentos e uso pela base de conhecimento no bot.

---

## 3. Agente por canal (Telegram / WhatsApp)

Arquivo: **`database/schema_agent_per_channel.sql`**

- Adiciona a coluna **`agent_id`** em:
  - `tenant_telegram_config`
  - `tenant_whatsapp_config`
  - `tenant_evolution_config`

Necessário para: escolher qual agente responde em cada canal (Telegram vs WhatsApp).

---

## 4. Documentos estendidos (se a tabela `documents` já existia sem essas colunas)

Arquivo: **`database/migration_documents.sql`**

- Adiciona em **`documents`**: `file_name`, `file_size_mb`, `file_type`, `source_url`, `status`
- Só rode se a tabela `documents` foi criada por uma versão antiga do `schema.sql` (sem essas colunas)

Se você rodou o **schema.sql** atual (que já traz a tabela `documents` completa), pode **pular** este passo.

---

## Resumo rápido

| Ordem | Arquivo                     | Quando usar                          |
|-------|-----------------------------|--------------------------------------|
| 1     | `schema.sql`                | Sempre (primeira vez ou ambiente novo) |
| 2     | `schema_pgvector.sql`       | Para base de conhecimento (RAG)     |
| 3     | `schema_agent_per_channel.sql` | Para agente por canal (Telegram/WhatsApp) |
| 4     | `migration_documents.sql`   | Só se `documents` já existia sem as colunas novas |

Depois de rodar, faça um deploy ou reinicie a API para usar as novas tabelas/colunas.
