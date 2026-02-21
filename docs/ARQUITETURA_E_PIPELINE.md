# Como o projeto está rodando — estrutura, pipeline, Vercel e Supabase

Documento para apoio à **migração de plataforma**. Descreve onde cada peça roda, como se conectam e o que replicar na nova infra.

---

## 1. Visão geral

| Camada | Onde roda | Tecnologia |
|--------|-----------|------------|
| **Frontend (Dashboard)** | Vercel (projeto separado) | Next.js, React |
| **API (Backend)** | Vercel (projeto separado) ou Railway/Render | FastAPI (Python) |
| **Banco de dados** | Supabase (Postgres) | PostgreSQL + pgvector |
| **Pipeline / CI** | Nenhum no repo | Deploy por push (Vercel auto-deploy) |
| **LLM / Embeddings** | APIs externas | OpenRouter, OpenAI |

Não há GitHub Actions nem outro CI no repositório: o deploy é feito pela Vercel ao dar push no GitHub (dois projetos linkados ao mesmo repo).

---

## 2. Estrutura do repositório (monorepo)

```
B&B RAG/
├── api/
│   ├── index.py              # Entrypoint Vercel da API (repassa para platform_backend)
│   └── requirements.txt
├── platform_backend/         # Backend FastAPI (auth, agentes, documentos, webhooks)
│   ├── main.py               # App FastAPI; usado por api/index.py na Vercel
│   ├── config.py
│   ├── db.py                 # Conexão Postgres (PLATFORM_DATABASE_URL / DATABASE_URL)
│   ├── auth.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── agents.py
│   │   ├── documents.py
│   │   ├── telegram_webhook.py
│   │   └── ...
│   └── requirements.txt
├── execution/                # Lógica de negócio (RAG, LLM, sessões) — usada pela API
│   ├── agent_facade.py
│   ├── llm_orchestrator.py
│   ├── knowledge_rag.py
│   ├── db_sessions.py        # Conexão Postgres (DATABASE_URL)
│   └── ...
├── frontend_dashboard/       # Dashboard Next.js (Root Directory na Vercel = este folder)
│   ├── app/
│   ├── lib/
│   │   └── api.ts            # Cliente HTTP; same-origin /api + rewrite para BACKEND_URL
│   └── package.json
├── database/                 # Schemas e migrations (rodar manualmente no Postgres)
│   ├── schema.sql
│   ├── schema_pgvector.sql
│   ├── schema_usage.sql
│   ├── schema_agent_per_channel.sql
│   ├── migration_documents.sql
│   └── migration_agents_embedding_namespace.sql
├── directives/               # Markdown usados pelo LLM (SPIN, RAG, etc.)
├── vercel.json               # Config do projeto API na Vercel (raiz do repo)
├── requirements.txt          # Deps Python (raiz)
└── run_platform_backend*.py  # Para rodar API local ou em servidor (Railway, VPS)
```

- **API na Vercel:** o `vercel.json` na raiz aponta para `platform_backend/main.py` (ou, em outra configuração, para `api/index.py`, que só importa `app` de `platform_backend.main`). Ou seja: um único backend FastAPI, servido como serverless.
- **Dashboard na Vercel:** é um **segundo projeto** na Vercel com **Root Directory** = `frontend_dashboard`. Esse projeto não usa o `vercel.json` da raiz.

---

## 3. Pipeline (deploy)

- **CI/CD:** não há `.github/workflows` nem outro pipeline no repositório.
- **Deploy:**
  - **Projeto 1 (API):** repositório conectado à Vercel com **Root Directory** em branco (raiz). A cada push na branch configurada (ex.: `main`), a Vercel faz build do backend Python e publica.
  - **Projeto 2 (Dashboard):** mesmo repositório, **Root Directory** = `frontend_dashboard`. A cada push, a Vercel faz `npm run build` e publica o Next.js.

Resumo: dois projetos Vercel, mesmo repo, dois roots diferentes; sem pipeline explícito além do deploy automático da Vercel.

---

## 4. Vercel — dois projetos

### 4.1 Projeto API (backend)

- **Root Directory:** vazio (raiz do repo).
- **Build:** definido pelo `vercel.json` (ex.: `platform_backend/main.py` com `@vercel/python`).
- **Variáveis de ambiente (principais):**
  - `DATABASE_URL` ou `PLATFORM_DATABASE_URL` — connection string Postgres (Supabase).
  - `PLATFORM_JWT_SECRET` — secret do JWT.
  - `TELEGRAM_WEBHOOK_BASE_URL` — URL pública da API (ex.: `https://bnb-rag-api.vercel.app`).
  - `OPENROUTER_API_KEY`, `OPENROUTER_MODEL` — LLM.
  - `OPENAI_API_KEY` — embeddings (e áudio, se usar).
  - `VERCEL=1` — detectado pela Vercel; usado no código (ex.: upload em `/tmp`).
- **Entrada:** todas as rotas `/(.*)` vão para o backend Python (FastAPI). Path pode ser ajustado por middleware (ex.: garantir `/api`).

### 4.2 Projeto Dashboard (frontend)

- **Root Directory:** `frontend_dashboard`.
- **Build:** Next.js (`npm run build`).
- **Variável crítica:** `BACKEND_URL` = URL do projeto API (ex.: `https://bnb-rag-api.vercel.app`), **sem** `/api` no final.
- **Comportamento:** o frontend chama `/api/...` na mesma origem; o Next.js deve fazer **rewrite** de `/api/*` para `BACKEND_URL/api/*` (configuração de rewrites no `next.config`). Se o `next.config` atual não tiver rewrites, é preciso adicionar algo como:
  - `rewrites: () => [{ source: '/api/:path*', destination: `${process.env.BACKEND_URL}/api/:path*` }]`.

---

## 5. Supabase (banco de dados)

- **Uso:** PostgreSQL hospedado no Supabase. A connection string é a mesma para API e para o módulo `execution` (sessões, RAG, etc.).
- **URL:** em geral `https://....supabase.com`; o código adiciona `?sslmode=require` quando o host é `supabase.com` e não há query string.
- **Variáveis:**
  - **API (platform_backend):** `PLATFORM_DATABASE_URL` ou `DATABASE_URL`.
  - **Execution (db_sessions, tenant_config, etc.):** `DATABASE_URL`.
  Na prática, para tudo funcionar junto, costuma-se usar a **mesma** connection string em ambas (ou definir as duas no mesmo ambiente).

### Schemas e migrations (ordem sugerida)

1. `database/schema.sql` — tenants, agents, conversations, documents, platform_users, etc.
2. `database/schema_pgvector.sql` — extensão `vector`, tabela `document_chunks`.
3. `database/schema_usage.sql` — uso e limites por plano.
4. `database/schema_agent_per_channel.sql` — colunas `agent_id` em configs Telegram/WhatsApp.
5. `database/migration_documents.sql` — colunas extras em `documents` (file_name, status, etc.).
6. `database/migration_agents_embedding_namespace.sql` — coluna `embedding_namespace` em `agents`.

Execução manual (ex.: `psql $DATABASE_URL -f database/arquivo.sql` ou SQL Editor do Supabase).

---

## 6. Fluxo de requisições

1. **Usuário acessa o dashboard** (ex.: `https://bnb-rag-bot.vercel.app`).
2. **Login/API:** o frontend envia requests para `/api/auth/login`, `/api/agents`, etc. (mesma origem).
3. **Next.js** reescreve `/api/*` para `BACKEND_URL/api/*` (ex.: `https://bnb-rag-api.vercel.app/api/...`).
4. **API (Vercel)** recebe a requisição, valida JWT, acessa Postgres (`PLATFORM_DATABASE_URL` / `DATABASE_URL`) e, quando precisa de RAG/LLM, usa o código em `execution/` (que também usa `DATABASE_URL`).
5. **Webhooks (Telegram/WhatsApp):** o provedor chama a URL pública da API (ex.: `TELEGRAM_WEBHOOK_BASE_URL/api/webhook/telegram/{tenant_id}`). A API processa e pode chamar OpenRouter/OpenAI e ler/escrever no Postgres.

---

## 7. Serviços externos (APIs)

- **OpenRouter:** LLM (respostas do agente). Variáveis: `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`.
- **OpenAI:** embeddings (base de conhecimento) e, se configurado, áudio. Variável: `OPENAI_API_KEY`.
- **Telegram / WhatsApp:** entrada de mensagens via webhook na URL da API; não exigem deploy separado.

---

## 8. O que replicar na migração

- **Dois deploys:** um para o backend (FastAPI), outro para o frontend (Next.js), ou equivalente (ex.: mesmo host com reverse proxy).
- **Uma connection string Postgres** usada tanto pelo backend quanto pelo `execution` (ou duas iguais: `DATABASE_URL` e `PLATFORM_DATABASE_URL`).
- **Variáveis de ambiente** listadas acima (JWT, URLs públicas, OpenRouter, OpenAI, etc.).
- **Rewrites no frontend:** se o dashboard e a API forem origens diferentes, manter o padrão “chamar `/api/*` na mesma origem e reescrever para a URL do backend”.
- **Schemas e migrations** aplicados na mesma ordem no novo Postgres.
- **Arquivos estáticos/upload:** na Vercel o backend usa `/tmp` quando `VERCEL=1`; na nova plataforma definir um diretório de upload (ex.: `PLATFORM_UPLOAD_DIR`) com permissão de escrita.

Com isso, você tem uma descrição objetiva de como o projeto está rodando (estrutura, pipeline, Vercel e Supabase) para replantar em outra plataforma.
