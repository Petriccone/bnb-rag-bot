# Onde rodar o bot 24/7 com RAG completo (independente do seu PC)

O bot pode rodar em qualquer lugar que execute Python e permita variáveis de ambiente. Para o **RAG (Google Drive)** funcionar sem arquivos no servidor, o projeto aceita credenciais por **variáveis de ambiente**.

---

## 1. Gerar o token do Google (uma vez, no seu PC)

Para usar o Drive em produção, você precisa gerar o `token.json` **uma vez** no seu computador e depois colar o conteúdo em uma variável de ambiente no servidor.

1. No seu PC, deixe `credentials.json` na raiz do projeto (baixado do Google Cloud Console).
2. Rode o bot ou um script que use o Drive (ex.: `python run_bot.py`) e faça o login no navegador quando pedir.
3. Após autorizar, será criado o arquivo **`token.json`** na raiz do projeto.
4. Abra `token.json`, copie **todo** o conteúdo (um JSON com `refresh_token`, `client_id`, `client_secret`, etc.).
5. Guarde esse texto para colar na variável **`GOOGLE_TOKEN_JSON`** no painel do serviço (Railway, Render, etc.).

**Importante:** não compartilhe esse conteúdo; ele dá acesso à sua pasta do Drive. Use apenas em variáveis de ambiente secretas do provedor.

---

## 2. Opções de hospedagem (com RAG funcionando)

### A) Railway (recomendado para começar)

- **Site:** [railway.app](https://railway.app)
- **Vantagem:** deploy por GitHub, variáveis de ambiente, Redis e Postgres opcionais no próprio Railway.
- **RAG:** funciona usando a variável **`GOOGLE_TOKEN_JSON`** (conteúdo do `token.json`).

**Passos:**

1. Crie um projeto e conecte o repositório GitHub.
2. **Variáveis de ambiente** (Settings → Variables). Exemplo:

   | Variável | Descrição |
   |----------|-----------|
   | `TELEGRAM_BOT_TOKEN` | Token do @BotFather |
   | `OPENROUTER_API_KEY` | Chave OpenRouter |
   | `OPENROUTER_MODEL` | Ex.: `openai/gpt-4o-mini` |
   | `DATABASE_URL` | Connection string Postgres (ex.: Supabase) |
   | `DRIVE_FOLDER_ID` | ID da pasta do Drive (RAG) |
   | **`GOOGLE_TOKEN_JSON`** | Conteúdo completo do arquivo `token.json` (um único texto em JSON) |
   | **`REDIS_URL`** | **Recomendado** — sem isso o bot responde uma mensagem por vez. Use Redis do Railway (Add Redis) ou Redis Labs. |
   | `MESSAGE_BUFFER_DEBOUNCE_SECONDS` | Opcional; ex.: `5` (segundos para juntar mensagens). |

3. **Start Command:** `python run_production.py`
4. Faça o deploy. O bot sobe e o RAG usa o Drive via `GOOGLE_TOKEN_JSON`.

---

### B) Render

- **Site:** [render.com](https://render.com)
- **Vantagem:** plano free para workers; integração com GitHub.
- **RAG:** mesmo esquema: defina **`GOOGLE_TOKEN_JSON`** com o conteúdo do `token.json`.

**Passos:**

1. New → Background Worker.
2. Conecte o repositório e defina o **Start Command:** `python run_production.py`.
3. Em **Environment**, adicione as mesmas variáveis da tabela acima (incluindo `GOOGLE_TOKEN_JSON`).
4. Deploy. O worker roda 24/7 e o RAG funciona com o Drive.

---

### C) Fly.io

- **Site:** [fly.io](https://fly.io)
- **Vantagem:** máquinas em várias regiões; volumes se precisar de arquivos depois.
- **RAG:** use **`GOOGLE_TOKEN_JSON`** nas secrets do app (`fly secrets set GOOGLE_TOKEN_JSON='...'`).

---

### D) VPS (DigitalOcean, Vultr, Linode, etc.)

- **Vantagem:** controle total; pode usar arquivos `credentials.json` e `token.json` normalmente, sem variáveis.
- **RAG:** funciona como no seu PC: coloque os arquivos na pasta do projeto e rode o bot (ex.: com systemd ou Docker).

**Resumo:** instale Python 3.10+, clone o repositório, copie `.env` e os arquivos do Drive para o servidor, execute `pip install -r requirements.txt` e `python run_production.py` (ou configure um serviço systemd para reiniciar em caso de queda).

---

## 3. Variáveis obrigatórias para RAG em produção

Para o RAG (Drive) funcionar **sem arquivos** no servidor:

| Variável | Onde pegar |
|----------|------------|
| **`GOOGLE_TOKEN_JSON`** | Conteúdo completo do `token.json` gerado no seu PC (após OAuth). Cole como uma única linha/string no painel. |
| `DRIVE_FOLDER_ID` | ID da pasta do Google Drive com a base de conhecimento (da URL da pasta). |

Não é necessário `GOOGLE_CREDENTIALS_JSON` em produção se você já tiver o `token.json` (ele contém o que precisa para refresh). Só use `credentials.json` (ou essa variável) no PC para gerar o primeiro `token.json`.

---

## 4. Resumo rápido

- **Rodar 24/7 com RAG completo:** use **Railway**, **Render** ou **Fly.io** e defina **`GOOGLE_TOKEN_JSON`** com o conteúdo do `token.json` gerado no seu PC.
- **Máximo controle e arquivos no disco:** use uma **VPS** e deixe `credentials.json` e `token.json` na pasta do projeto como no desenvolvimento.

Qualquer uma dessas opções deixa o bot rodando independente do seu computador, com RAG funcionando.

---

## 5. Deploy na Vercel (produção)

Para subir o **dashboard** e a **API** na Vercel em modo produção, use **dois projetos** (mesmo repositório): um para o backend (FastAPI) e outro para o frontend (Next.js). Passo a passo e variáveis: **[docs/DEPLOY_VERCEL.md](docs/DEPLOY_VERCEL.md)**.

---

## 6. Platform (dashboard) — Telegram por token

Se você usa o **dashboard** e a opção **Conexão Telegram** (usuário cola o token do bot e o bot começa a rodar):

1. **Banco:** execute o schema em `database/schema.sql` no seu Postgres (inclui a tabela `tenant_telegram_config`).
2. **URL do webhook:** defina **`TELEGRAM_WEBHOOK_BASE_URL`** com a URL pública do backend (ex.: `https://seu-dominio.com`). O Telegram envia as mensagens para `{TELEGRAM_WEBHOOK_BASE_URL}/api/webhook/telegram/{tenant_id}`. Se não definir, o sistema usa `WHATSAPP_WEBHOOK_BASE_URL`.
