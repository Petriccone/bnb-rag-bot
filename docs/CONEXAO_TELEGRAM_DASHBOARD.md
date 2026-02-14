# Análise Completa e Solução para Conexão Telegram via Dashboard

Documento de referência: diagnóstico do problema "Token Inválido", formas de conectar e requisitos para o app funcionar.

---

## Diagnóstico: Por que "Token Inválido"?

O token **é válido** — comprovado chamando a API do Telegram diretamente:

```python
python -c "import httpx; r = httpx.get('https://api.telegram.org/botSEU_TOKEN/getMe', timeout=10); print(r.status_code, r.text)"
# 200 {"ok":true,"result":{"id":...,"is_bot":true,"username":"..."}}
```

O problema está na **transmissão do token** do navegador → backend. Possíveis causas:

| Causa | Descrição |
|-------|-----------|
| **Encoding do JSON** | Caracteres como `-` ou `_` podem ser alterados pelo navegador/proxy |
| **Hífens Unicode** | Ao colar de WhatsApp/Word, o hífen `-` vira `–` (en-dash) ou `—` (em-dash) |
| **Espaços invisíveis** | BOM, zero-width space, non-breaking space ao colar |
| **Truncamento** | O token pode ser cortado se o campo tiver `maxLength` ou CSS que esconde texto |

---

## Solução Implementada: 4 Formas de Conectar

Para eliminar o problema de encoding, o cliente pode enviar o token de 4 formas:

### 1. Token do servidor (`.env`) — Mais confiável

O admin coloca o token no `.env` e o cliente clica em um botão:

```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_WEBHOOK_BASE_URL=https://sua-url-publica.com
```

O backend lê direto do `.env` — zero risco de encoding.

### 2. Colar no campo → enviado em Base64

O frontend converte para base64 antes de enviar; o backend decodifica. Evita corrupção no JSON.

### 3. Upload de arquivo `.txt`

O cliente salva o token num `.txt` e faz upload — contorna totalmente o problema de colar.

### 4. Header HTTP

Para integrações via API:

```
X-Telegram-Bot-Token: 123456:ABC...
```

---

## Requisito Obrigatório: URL Pública do Backend

O Telegram **exige HTTPS e URL pública** para webhooks. Sem isso, a conexão pelo dashboard não funciona.

### Em teste local (ngrok)

```powershell
# 1. Instalar ngrok
winget install ngrok.ngrok

# 2. Configurar authtoken (uma vez)
ngrok config add-authtoken SEU_TOKEN

# 3. Expor o backend
ngrok http 8000

# 4. Copiar a URL HTTPS e colocar no .env
# TELEGRAM_WEBHOOK_BASE_URL=https://xxxx.ngrok-free.app
```

### Em produção

```env
TELEGRAM_WEBHOOK_BASE_URL=https://api.seudominio.com
```

---

## Modo Alternativo: Bot sem Dashboard (Long Polling)

O bot **funciona sem dashboard e sem webhook** usando `run_bot.py`:

```powershell
cd "c:\Users\rsp88\B&B RAG"
python run_bot.py
```

Isso usa **long polling** — não precisa de URL pública nem de ngrok. É o modo que funciona sem configuração de webhook.

---

## Resumo das Alterações nos Arquivos

**Backend (`platform_backend/routers/telegram.py`):**
- Aceita token via `bot_token`, `botToken`, `bot_token_b64` (base64), `use_server_token`, header `X-Telegram-Bot-Token`
- Normaliza hífens Unicode para ASCII; `strip()` e remove espaços no meio
- Valida via `setWebhook` (se o Telegram aceitar, o token é válido)
- Endpoint `POST /connect-with-file` para upload de `.txt`
- Mensagem de erro inclui quantidade de caracteres recebidos (diagnóstico)

**Frontend (`frontend_dashboard/app/dashboard/telegram/page.tsx`):**
- Ícone de olho no campo do token (mostrar/ocultar)
- Token enviado em base64 ao colar
- Botão "Conectar com token do servidor"
- Upload de arquivo `.txt`
- Aviso sobre confusão `1` vs `l` quando erro de token
- Bloco em destaque: "Fazer o bot responder" com instrução `python run_bot.py`

**.env (exemplo):**
```env
TELEGRAM_BOT_TOKEN=123456:ABC...
TELEGRAM_WEBHOOK_BASE_URL=https://sua-url.ngrok-free.app
```

---

## Para o App Funcionar Agora

```
┌─────────────────────────────────────────────────┐
│ 1. Terminal A: ngrok http 8000                  │
│    → copiar URL HTTPS → colar no .env            │
│                                                 │
│ 2. Terminal B: python run_platform_backend.py   │
│    (na pasta raiz do projeto)                  │
│                                                 │
│ 3. Terminal C: cd frontend_dashboard            │
│    → .\run_dev.ps1                              │
│                                                 │
│ 4. Navegador: Dashboard → Conexão Telegram       │
│    → "Conectar com token do servidor"            │
│                                                 │
│ 5. Telegram: enviar mensagem para o bot          │
└─────────────────────────────────────────────────┘
```

**Nota:** No plano gratuito do ngrok, a URL muda ao reiniciar. Se fechar o ngrok, atualize o `.env` com a nova URL e reinicie o backend. Em produção, use um domínio fixo.
