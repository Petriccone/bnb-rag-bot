# Agente SDR Telegram — Filtros de Água (SPIN Selling)

Bot consultivo de vendas para Telegram com suporte a **texto e áudio**, metodologia **SPIN Selling** e base de conhecimento no **Google Drive**.

## Arquitetura (3 camadas)

- **Camada 1 — Diretivas**: SOPs em `directives/` (personalidade, SPIN, RAG, imagens, fechamento, pós-venda, áudio).
- **Camada 2 — Orquestração**: Lógica do bot em Python que aplica estados, chama scripts e o LLM.
- **Camada 3 — Execução**: Scripts em `execution/` (Telegram, STT, TTS, Drive RAG, DB, state machine, LLM).

## Requisitos

- Python 3.10+
- **OpenRouter** para o chat (LLM) — chave em [openrouter.ai](https://openrouter.ai)
- **OpenAI** apenas se for usar áudio (Whisper STT e TTS)
- Bot no Telegram (token via [@BotFather](https://t.me/BotFather))
- Opcional: pasta no Google Drive com base de conhecimento + OAuth (credentials.json)

## Instalação

```bash
cd "B&B RAG"
pip install -r requirements.txt
```

## Configuração

1. Copie o arquivo de exemplo e preencha as variáveis:

   ```bash
   copy .env.example .env
   ```

2. **.env** (obrigatório para o bot):

   - `TELEGRAM_BOT_TOKEN` — token do bot (BotFather).
   - `OPENROUTER_API_KEY` — chave em [openrouter.ai](https://openrouter.ai) (chat/LLM).
   - `OPENROUTER_MODEL` — modelo (ex.: `openai/gpt-4o-mini`, `anthropic/claude-3-haiku`). Padrão: `openai/gpt-4o-mini`.
   - `OPENAI_API_KEY` — só se for usar áudio (Whisper + TTS); deixe vazio para só texto.

3. **Banco de dados (opcional — Supabase)**:

   - Se quiser usar **Supabase** em vez de SQLite, defina no `.env`:
     - `SUPABASE_URL` — URL do projeto (ex.: `https://xxxxx.supabase.co`).
     - `SUPABASE_SERVICE_ROLE_KEY` — chave "service_role" (em Project Settings → API). Não use a chave "anon" no servidor.
   - No Supabase: **SQL Editor** → New query → cole e execute o conteúdo do arquivo `execution/supabase_schema.sql` para criar as tabelas `sessions` e `conversation_log`.
   - Se não definir essas variáveis, o bot usa **SQLite** (arquivo `.tmp/sdr_bot.db`).

4. **Google Drive (RAG)**:

   - Crie um projeto no [Google Cloud Console](https://console.cloud.google.com/), ative a **Google Drive API** e crie credenciais OAuth 2.0 (aplicativo desktop).
   - Baixe o JSON e salve na raiz do projeto como `credentials.json`.
   - Na primeira execução que usar o Drive, será aberto o fluxo OAuth no navegador; após autorizar, será gerado o `token.json`.
   - Crie uma pasta no Drive com os materiais (FAQ, preços, benefícios, links de pagamento, etc.) e defina no .env:
     - `DRIVE_FOLDER_ID` — ID da pasta (ex.: da URL `https://drive.google.com/drive/folders/XXXXXXXX` use `XXXXXXXX`).

5. **Imagens dos produtos** (opcional):

   - Crie `.tmp/products.json` com a lista de modelos para envio de fotos. Exemplo:

   ```json
   [
     {
       "nome": "Modelo A",
       "indicacao": "Ideal para cozinha com pouco espaço.",
       "diferencial": "Dupla filtração, remove cloro e partículas.",
       "preco": "R$ 299",
       "image_url": "https://exemplo.com/img-a.jpg"
     }
   ]
   ```

   - `image_url` pode ser URL ou caminho local; `nome` deve bater com o que o LLM retornar em `modelos`.

## Como rodar o bot

Na raiz do projeto:

```bash
python run_bot.py
```

Ou:

```bash
python -m execution.telegram_handler
```

(no segundo caso, defina `PYTHONPATH` para a raiz ou execute de dentro da raiz.)

O bot usa **long polling**. No Telegram, envie `/start` e converse por texto ou áudio.

**Modo produção (reinício automático + log em arquivo):**
```bash
python run_production.py
```

## Deploy no Railway (rodar 24/7 sem depender do seu PC)

1. **Crie uma conta** em [railway.app](https://railway.app) e um novo projeto.

2. **Conecte o repositório** (GitHub/GitLab) ou faça deploy manual (Railway CLI: `railway init` e `railway up`).

3. **Configure o comando de start** no serviço:
   - Em **Settings** do serviço → **Deploy** → **Start Command**: `python run_production.py`
   - Ou use o `Procfile`: o Railway pode usar o processo `worker` (comando: `python run_production.py`).

4. **Variáveis de ambiente** (Settings → Variables). Adicione as mesmas do seu `.env`:

   | Variável | Obrigatório | Descrição |
   |----------|-------------|-----------|
   | `TELEGRAM_BOT_TOKEN` | Sim | Token do @BotFather |
   | `OPENROUTER_API_KEY` | Sim | Chave OpenRouter (LLM) |
   | `OPENROUTER_MODEL` | Sim | Ex.: `openai/gpt-4o-mini` ou `deepseek/deepseek-v3.2` |
   | `DATABASE_URL` | Recomendado | Connection string Postgres (ex.: Supabase). No Railway pode usar o Postgres nativo ou seu Supabase. |
   | `REDIS_URL` | Opcional | Redis para buffer (debounce). Pode usar Redis do Railway ou Redis Labs. |
   | `DRIVE_FOLDER_ID` | Opcional | ID da pasta do Google Drive (RAG). |
   | `RUN_MODE` | Opcional | `production` para log em arquivo (no Railway o log vai para o painel). |

   **Google Drive (RAG):** o bot espera `credentials.json` e `token.json` no projeto. No Railway você pode: gerar o `token.json` no seu PC (uma vez), colar o conteúdo em uma variável e ajustar o código para ler de variável; ou usar um volume/arquivo de configuração se o Railway oferecer.

5. **Banco:** use **Supabase** (já configurado no seu caso) com `DATABASE_URL` no formato `postgresql://...`. Crie as tabelas com `execution/supabase_schema.sql` no SQL Editor do Supabase.

6. **Deploy:** após salvar as variáveis, o Railway faz o build (instala `requirements.txt`) e inicia o bot. O serviço fica rodando 24/7; em caso de queda, o `run_production.py` reinicia o processo.

**Dica:** no Railway, o tipo do serviço é **worker** (não precisa abrir porta HTTP). Se o painel pedir um "Web Service", defina apenas o Start Command; o bot não usa `PORT`.

**RAG (Google Drive) no Railway:** para o bot usar a base do Drive em produção, defina a variável **`GOOGLE_TOKEN_JSON`** com o conteúdo completo do arquivo `token.json` (gerado uma vez no seu PC após OAuth). Veja o guia completo em **[DEPLOY.md](DEPLOY.md)** — onde rodar 24/7 com RAG funcionando (Railway, Render, Fly.io, VPS).

## Fluxo do agente

1. **Entrada**: mensagem de texto ou áudio.
2. Se for áudio: download → Whisper (STT) → texto.
3. Sessão e estado SPIN são carregados (DB).
4. Busca no Drive (RAG) com a mensagem e o estado atual.
5. LLM recebe diretivas + estado + contexto RAG + histórico e devolve resposta em JSON (texto, próximo estado, enviar áudio, enviar imagens, modelos).
6. Estado é atualizado só se a transição for válida (nunca pular etapa).
7. Resposta em texto é enviada; se for fase de oferta, podem ser enviadas 2–3 imagens de modelos; se a entrada foi áudio, a resposta é também convertida em áudio (TTS) e enviada.

## Estados SPIN (ordem fixa)

`descoberta` → `problema` → `implicacao` → `solucao` → `oferta` → `fechamento` → `pos_venda`

## Banco de dados

- **SQLite** (padrão): arquivo `.tmp/sdr_bot.db` (ou `DATABASE_PATH`). Criado automaticamente.
- **Supabase**: se `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` estiverem no `.env`, o bot usa Supabase. Execute `execution/supabase_schema.sql` no SQL Editor do projeto para criar as tabelas `sessions` e `conversation_log`.

## Message Buffer (debounce)

Se **REDIS_URL** estiver definido no `.env`, mensagens de **texto** são agrupadas antes de chamar o CORE: o adapter espera uma janela (3–4 s), consolida várias mensagens em uma e dispara **uma única** resposta. Áudio não passa pelo buffer.

- **Directive**: `directives/message_buffering.md`
- **Execution**: `execution/message_buffer.py` (Redis, chave `buffer:{tenant_id}:{user_id}`)
- **Adapter**: `execution/telegram_buffer_adapter.py` (agendamento assíncrono, chama `run_agent` após o flush)
- **Logs**: `buffer_created`, `buffer_extended`, `buffer_flushed`, `buffer_timeout_triggered`
- **Testes**: `python tests/test_message_buffer.py` (com Redis para testar consolidação)

## Documentação das diretivas

As regras do agente estão em `directives/` em Markdown. Alterações ali mudam o comportamento sem precisar alterar código.
