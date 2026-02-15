# Deploy na Vercel (modo produção)

O projeto usa **dois aplicativos**: frontend (Next.js) e backend (FastAPI). Você precisa de **dois projetos** na Vercel (ou API no Railway). O dashboard faz **proxy** de `/api/*` para o backend quando `BACKEND_URL` está definido.

## Refatoração (entrada da API)

- **Entrada única:** `api/index.py` — o `vercel.json` na raiz encaminha todas as rotas para esse arquivo.
- **Imports lentos:** `psycopg2`, `bcrypt` e `jose` são importados só quando usados, para o cold start na Vercel não falhar.
- **Config:** Se `pydantic_settings` ou `.env` falharem, o backend usa variáveis de ambiente direto.

---

## Visão geral

| Projeto   | Root Directory     | URL exemplo              | Função                          |
|-----------|---------------------|--------------------------|----------------------------------|
| **API**   | (em branco = raiz)  | `https://bnb-rag-api.vercel.app` | FastAPI (login, webhook, etc.) |
| **Dashboard** | `frontend_dashboard` | `https://bnb-rag-bot.vercel.app` | Next.js; faz proxy de `/api/*` para a API |

No projeto **Dashboard**, defina `BACKEND_URL` = URL do projeto API (sem `/api` no final). O frontend chama a mesma origem (`/api/...`); o Next.js encaminha para o backend.

### Se você já tem só o dashboard (ex.: bnb-rag-bot) e dá 404 em /health ou 405 no cadastro

1. **Criar o projeto da API:** na Vercel → **Add New** → **Project** → mesmo repositório. Nome sugerido: `bnb-rag-api`.
2. **Configurar o projeto da API:** **Root Directory** = em branco. **Framework Preset** = Other. Variáveis: `DATABASE_URL`, `PLATFORM_JWT_SECRET`, etc. (como na seção 1 abaixo). **Deploy**.
3. **Configurar o dashboard:** no projeto do dashboard (bnb-rag-bot) → **Settings** → **Environment Variables** → adicionar **`BACKEND_URL`** = URL do projeto da API (ex.: `https://bnb-rag-api.vercel.app`), sem `/api` no final.
4. **Redeploy** do dashboard. Testar login/cadastro de novo.

---

## Backend em produção: duas estratégias

| Estratégia | Quando usar | Comando / Onde |
|------------|-------------|----------------|
| **Vercel (serverless)** | Dashboard + API na Vercel, escala automática, sem servidor 24/7 | Deploy do projeto API na Vercel (abaixo). Já é produção ao publicar. |
| **Self-hosted (Railway, Render, VPS)** | Controle total, worker do buffer (Redis) ativo, sempre no ar | `python run_platform_backend_production.py` com variáveis de ambiente. |

- **Vercel:** não precisa de script; o backend sobe como função serverless. Configure `DATABASE_URL`, `PLATFORM_JWT_SECRET`, etc. no painel.
- **Self-hosted:** use `run_platform_backend_production.py` (sem `reload`, host/porta por env). Variáveis opcionais: `PLATFORM_HOST=0.0.0.0`, `PLATFORM_PORT=8000`, `LOG_LEVEL=info`.

---

## 1. Projeto 1 — API (backend)

O backend precisa estar no ar primeiro, para você usar a URL dele no frontend.

### No painel da Vercel

1. **New Project** → importe o repositório.
2. **Root Directory:** deixe em branco (raiz do repo).
3. **Framework Preset:** Other (ou None). Não use Next.js aqui.
4. **Build Command:** vazio. O `vercel.json` na raiz aponta para `api/index.py`; a Vercel instala deps com `pip install -r requirements.txt` e invoca essa função para todas as rotas.
5. **Install Command:** `pip install -r requirements.txt` (se quiser garantir).
6. **Output Directory:** vazio.

### Variáveis de ambiente (Settings → Environment Variables)

| Variável | Obrigatório | Descrição |
|----------|------------|-----------|
| `DATABASE_URL` ou `PLATFORM_DATABASE_URL` | Sim | Connection string Postgres (ex.: Supabase, Neon). |
| `PLATFORM_JWT_SECRET` | Sim | Secret forte para JWT (ex.: string longa aleatória). |
| `TELEGRAM_WEBHOOK_BASE_URL` | Sim* | URL pública deste backend (ex.: `https://seu-projeto-api.vercel.app`). O Telegram envia updates para `{esta_url}/api/webhook/telegram/{tenant_id}`. |
| `OPENROUTER_API_KEY` | Sim** | Para o agente responder (LLM). |
| `OPENROUTER_MODEL` | Não | Ex.: `openai/gpt-4o-mini`. |
| `OPENAI_API_KEY` | Não | Para STT/Whisper e TTS se usar áudio. |
| `DRIVE_FOLDER_ID` | Não | RAG com Google Drive. |
| `GOOGLE_TOKEN_JSON` | Não | Conteúdo do `token.json` (para RAG em produção). |
| `REDIS_URL` | Não | Buffer de mensagens (debounce). Na Vercel o worker do buffer não roda; sem Redis cada mensagem é respondida na hora. |

\* Necessário para Conexão Telegram pelo dashboard.  
\** Necessário para o agente gerar respostas.

### Deploy

- **Deploy** e anote a URL do projeto (ex.: `https://bbrag-api-xxx.vercel.app`).
- Teste: `https://sua-url-api.vercel.app/health` deve retornar `{"status":"ok"}`.

### Se a API retornar 500 (FUNCTION_INVOCATION_FAILED)

- O backend usa **import lazy** de `psycopg2` (só ao acessar o banco), para o cold start na Vercel não falhar.
- Confira no projeto da API: **Settings → Environment Variables** → existem **`DATABASE_URL`** (ou `PLATFORM_DATABASE_URL`) e **`PLATFORM_JWT_SECRET`**?
- Sem `DATABASE_URL`, rotas que usam banco (login, cadastro, etc.) falham; `/` e `/health` devem responder mesmo assim.

### Se POST /api/auth/register retornar 405 (Method Not Allowed)

Na Vercel, o runtime Python às vezes repassa o path errado para o FastAPI, e o POST pode cair em GET `/` e devolver 405.

**Diagnóstico:** abra no navegador:

- `https://sua-url-api.vercel.app/` → deve aparecer algo como `{"message":"B&B RAG Platform API", ...}`.
- `https://sua-url-api.vercel.app/health` → deve aparecer `{"status":"ok"}`.

Se **não** aparecer isso (404, página em branco ou outro domínio), o **Projeto 1** não está servindo o backend: confira **Root Directory** (em branco = raiz do repo) e **Framework Preset** (Other). Refaça o deploy.

Se GET `/` e `/health` **funcionam** mas o cadastro/login continua 405, use o backend **fora da Vercel**:

1. Suba a API no **Railway** (ou Render/Fly.io): mesmo repo, root em branco, comando `python run_platform_backend_production.py`, variáveis iguais ao Projeto 1.
2. No **Projeto 2 (Dashboard)**, em variáveis de ambiente, defina `NEXT_PUBLIC_API_URL` = URL do backend no Railway (ex.: `https://seu-app.railway.app`), **sem** `/api` no final.
3. Faça redeploy do dashboard. O front passa a chamar o backend no Railway e o 405 some.

---

## 2. Projeto 2 — Dashboard (frontend)

1. **New Project** → mesmo repositório.
2. **Root Directory:** `frontend_dashboard`.
3. **Framework Preset:** Next.js (detectado automaticamente).
4. **Build Command:** `npm run build` (padrão).
5. **Output Directory:** `.next` (padrão).

### Variáveis de ambiente (obrigatório para login/cadastro)

| Variável | Valor |
|----------|--------|
| **`BACKEND_URL`** | URL do **Projeto 1 (API)** sem barra no final. Ex.: `https://bnb-rag-api.vercel.app` |

Com isso, o Next.js faz **rewrite** de `/api/*` para `BACKEND_URL/api/*`. O frontend chama a mesma origem; não é necessário definir `NEXT_PUBLIC_API_URL` (pode ficar em branco).

### Deploy

- **Deploy** e abra a URL do frontend (ex.: `https://bbrag-dashboard-xxx.vercel.app`).
- Faça login/registro; a autenticação vai para a API na Vercel.

---

## 3. Telegram (webhook)

1. No **Projeto 1 (API)** confirme que `TELEGRAM_WEBHOOK_BASE_URL` é exatamente a URL do backend (ex.: `https://bbrag-api-xxx.vercel.app`), **sem** `/api` no final.
2. No dashboard (Projeto 2), em **Conexão Telegram**, conecte com o token do bot. O sistema registra o webhook em `{TELEGRAM_WEBHOOK_BASE_URL}/api/webhook/telegram/{tenant_id}`.
3. Se o bot não responder, confira os **Logs** do Projeto 1 na Vercel (Requests → função que trata o webhook).

---

## 4. Banco de dados

- Execute o schema em `database/schema.sql` no seu Postgres (Supabase, Neon, etc.).
- Use a connection string em `DATABASE_URL` ou `PLATFORM_DATABASE_URL` no Projeto 1.

---

## 5. Token inválido no browser do Cursor

Se ao conectar o Telegram **no browser embutido do Cursor** aparecer "token inválido", mas **no navegador externo** funcionar, as causas mais comuns são:

- **Origem diferente:** o frontend no Cursor pode estar em `localhost` com porta diferente e a API pode rejeitar ou o CORS se comportar diferente.
- **Cookies / storage:** o browser do Cursor pode ter contexto isolado (sem cookies do seu domínio de produção).

**Recomendação:** usar o **navegador externo** para ações que dependem de API (conectar Telegram, etc.). Em produção (Vercel), ambos (dashboard e API) estarão no mesmo domínio lógico (URLs diferentes), então o problema de "token inválido" no Cursor tende a não ocorrer quando acessar a URL de produção no Chrome/Edge.

---

## Resumo

| O quê | Onde | URL exemplo |
|-------|------|-------------|
| API (FastAPI) | Projeto 1 — Root = repo | `https://bbrag-api.vercel.app` |
| Dashboard (Next.js) | Projeto 2 — Root = `frontend_dashboard` | `https://bbrag-dashboard.vercel.app` |

No Projeto 2 (Dashboard), defina **`BACKEND_URL`** = URL do Projeto 1 (ex.: `https://bnb-rag-api.vercel.app`). No Projeto 1 (API), defina **`TELEGRAM_WEBHOOK_BASE_URL`** = URL do Projeto 1.
