# Deploy na Vercel (modo produção)

O projeto usa **dois aplicativos**: frontend (Next.js) e backend (FastAPI). Na Vercel você sobe **dois projetos** a partir do mesmo repositório.

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
4. **Build Command:** vazio (a Vercel usa `index.py` na raiz e instala deps automaticamente).
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

---

## 2. Projeto 2 — Dashboard (frontend)

1. **New Project** → mesmo repositório.
2. **Root Directory:** `frontend_dashboard`.
3. **Framework Preset:** Next.js (detectado automaticamente).
4. **Build Command:** `npm run build` (padrão).
5. **Output Directory:** `.next` (padrão).

### Variáveis de ambiente

| Variável | Valor |
|----------|--------|
| `NEXT_PUBLIC_API_URL` | URL do **Projeto 1** (API), sem barra no final. Ex.: `https://bbrag-api-xxx.vercel.app` |

Assim o dashboard em produção chama a API no mesmo backend que você deployou.

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

No Projeto 2, `NEXT_PUBLIC_API_URL` = URL do Projeto 1. No Projeto 1, `TELEGRAM_WEBHOOK_BASE_URL` = URL do Projeto 1.
