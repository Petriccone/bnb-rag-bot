# B&B RAG Platform API - Backend Multi-tenant

API REST para plataforma SaaS B2B de automação de WhatsApp/Telegram com RAG (Retrieval Augmented Generation).

## Índice

- [Arquitetura Multi-tenant](#arquitetura-multi-tenant)
- [Autenticação](#autenticação)
- [API Reference](#api-reference)
  - [Auth](#auth)
  - [Tenants](#tenants)
  - [Agents](#agents)
  - [Documents](#documents)
  - [Usage Tracking](#usage-tracking)
  - [Metrics](#metrics)
- [Vector Store](#vector-store)
- [Deployment](#deployment)

## Arquitetura Multi-tenant

### Isolamento de Dados

- Cada tenant possui dados completamente isolados
- `tenant_id` é usado em todas as consultas SQL
- Vector store por tenant (namespace separado)
- Cache de embeddings isolado

### Middleware de Contexto

O `TenantContextMiddleware` injeta automaticamente:
- `tenant_id` no request.state
- `user_id` do token JWT
- `plan` do tenant

```python
from platform_backend.middleware import get_tenant_from_request

async def minha_rota(request: Request):
    tenant_id = get_tenant_from_request(request)
```

## Autenticação

### JWT Tokens

A API usa JWT para autenticação. O token deve ser enviado no header:

```
Authorization: Bearer <token_jwt>
```

### Criação de Token

```python
from platform_backend.auth import create_access_token

token = create_access_token({
    "sub": "user_id",
    "tenant_id": "tenant_uuid",
    "plan": "pro",
    "email": "user@example.com"
})
```

### Dependencies

Use as dependências do FastAPI para proteger rotas:

```python
from platform_backend.dependencies import CurrentUser, CurrentTenant

@router.get("/items")
def list_items(user: CurrentUser, tenant_id: CurrentTenant):
    # user = {"user_id": "...", "tenant_id": "...", "plan": "..."}
    ...
```

## API Reference

### Auth

#### POST /api/auth/register

Registra novo usuário e tenant.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword",
  "company_name": "My Company"
}
```

**Response:**
```json
{
  "id": "user_uuid",
  "email": "user@example.com",
  "tenant_id": "tenant_uuid",
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

#### POST /api/auth/login

Login com email e senha.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "access_token": "jwt_token",
  "token_type": "bearer"
}
```

---

### Tenants

#### GET /api/tenants

Lista informações do tenant atual.

**Response:**
```json
{
  "id": "tenant_uuid",
  "company_name": "My Company",
  "plan": "pro",
  "settings": {},
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### PATCH /api/tenants

Atualiza configurações do tenant.

**Request:**
```json
{
  "plan": "enterprise",
  "settings": {"key": "value"}
}
```

---

### Agents

#### GET /api/agents

Lista todos os agentes do tenant.

**Response:**
```json
[
  {
    "id": "agent_uuid",
    "tenant_id": "tenant_uuid",
    "name": "Sales Agent",
    "niche": "real_estate",
    "prompt_custom": "You are a...",
    "active": true
  }
]
```

#### POST /api/agents

Cria novo agente.

**Request:**
```json
{
  "name": "Sales Agent",
  "niche": "real_estate",
  "prompt_custom": "You are a helpful agent..."
}
```

#### GET /api/agents/{agent_id}

Obtém agente específico.

#### PATCH /api/agents/{agent_id}

Atualiza agente (pausar/ativar).

**Request:**
```json
{
  "name": "New Name",
  "active": false
}
```

#### DELETE /api/agents/{agent_id}

Deleta agente.

---

### Documents

#### GET /api/documents

Lista documentos do tenant.

**Response:**
```json
[
  {
    "id": "doc_uuid",
    "tenant_id": "tenant_uuid",
    "file_path": "/uploads/xxx.pdf",
    "file_name": "product_list.pdf",
    "file_size_mb": 2.5,
    "file_type": "pdf",
    "embedding_namespace": "tenant_uuid",
    "source_url": null,
    "status": "completed"
  }
]
```

#### POST /api/documents/upload

Faz upload de documento.

- **Form-data**: `file` (UploadFile)
- **Query**: `embedding_namespace` (opcional)

**Formatos suportados:**
- `.txt`, `.pdf`
- `.xlsx`, `.xls` (Excel)
- `.docx` (Word)
- `.csv`
- `.md` (Markdown)
- `.html`

**Response:**
```json
{
  "id": "doc_uuid",
  "status": "pending",
  ...
}
```

O processamento é assíncrono. Use `/api/documents/{id}/status` para verificar.

#### POST /api/documents/url

Faz upload de documento a partir de URL.

**Request:**
```json
{
  "url": "https://example.com/page.html",
  "embedding_namespace": "optional_namespace"
}
```

#### GET /api/documents/{document_id}/status

Verifica status do processamento.

**Response:**
```json
{
  "id": "doc_uuid",
  "status": "completed",
  "file_name": "document.pdf",
  "file_type": "pdf"
}
```

#### DELETE /api/documents/{document_id}

Deleta documento e seus chunks.

---

### Usage Tracking

#### GET /api/usage

Retorna uso atual do tenant no mês.

**Response:**
```json
{
  "year_month": "2024-01",
  "messages_used": 1500,
  "messages_limit": 2000,
  "tokens_used": 50000,
  "tokens_limit": 100000,
  "storage_mb": 25.5,
  "storage_limit_mb": 50,
  "documents_count": 8,
  "documents_limit": 10,
  "agents_count": 3,
  "agents_limit": 3,
  "plan": "free"
}
```

#### POST /api/usage/track/message

Registra mensagem enviada (uso interno).

#### POST /api/usage/track/tokens

Registra tokens usados (uso interno).

#### POST /api/usage/track/storage

Registra uso de storage.

#### GET /api/usage/logs

Retorna logs de uso.

**Query params:**
- `limit`: número de registros (default 50)
- `event_type`: filtrar por tipo

#### GET /api/usage/limits?plan=pro

Retorna limites de um plano.

**Response:**
```json
{
  "plan": "pro",
  "messages_limit": 10000,
  "tokens_limit": 500000,
  "storage_limit_mb": 500,
  "documents_limit": 50,
  "agents_limit": 10
}
```

---

### Metrics

#### GET /api/metrics

Retorna métricas agregadas do tenant.

**Response:**
```json
{
  "agents_count": 3,
  "conversations_count": 150,
  "leads_count": 45,
  "messages_this_month": 1200,
  "plan": "pro"
}
```

---

## Vector Store

### Configuração

O sistema usa PostgreSQL com extensão pgvector para armazenar embeddings.

### Namespace por Tenant

Cada tenant tem seu namespace de embeddings:
- Default: `tenant_{tenant_id}`
- Custom: especificado no upload

### Busca RAG

```python
from execution.knowledge_rag import search_document_chunks

context = search_document_chunks(
    tenant_id="tenant_uuid",
    query="qual o preço do produto X?",
    limit=6
)
```

### Índices

O schema inclui índices HNSW para busca por similaridade (cosine distance):

```sql
CREATE INDEX idx_document_chunks_embedding 
ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

## Deployment

### Variáveis de Ambiente

```env
# Banco de dados
DATABASE_URL=postgresql://...
PLATFORM_DATABASE_URL=postgresql://...

# JWT
PLATFORM_JWT_SECRET=sua_chave_secreta

# OpenAI (para embeddings)
OPENAI_API_KEY=sk-...

# Upload
PLATFORM_UPLOAD_DIR=.tmp/uploads

# Vercel
VERCEL=1
```

### Execute Migration

```bash
# Schema base
psql $DATABASE_URL -f database/schema.sql

# Schema pgvector
psql $DATABASE_URL -f database/schema_pgvector.sql

# Schema usage tracking
psql $DATABASE_URL -f database/schema_usage.sql

# Migration (se necessário)
psql $DATABASE_URL -f database/migration_documents.sql
```

### Run Server

```bash
# Development
python run_platform_backend.py

# Production
python run_platform_backend_production.py
```

## Planos

| Recurso | Free | Pro | Enterprise |
|---------|------|-----|------------|
| Mensagens/mês | 2,000 | 10,000 | Ilimitado |
| Tokens/mês | 100K | 500K | Ilimitado |
| Storage | 50MB | 500MB | Ilimitado |
| Agentes | 3 | 10 | Ilimitado |
| Documentos | 10 | 50 | Ilimitado |
