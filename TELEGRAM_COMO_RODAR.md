# Como fazer o bot Telegram funcionar

Para análise completa (diagnóstico "Token Inválido", 4 formas de conectar, ngrok, passo a passo), veja **`docs/CONEXAO_TELEGRAM_DASHBOARD.md`**.

## Para o cliente (dashboard): conectar o bot dele

O cliente entra no dashboard → **Conexão Telegram** e pode conectar de **4 formas**:

1. **Conectar com token do servidor** – Se o admin colocou `TELEGRAM_BOT_TOKEN` no `.env` do servidor, um clique e o webhook é registrado. (Recomendado quando há um único bot por servidor.)
2. **Colar o token** – O token é enviado em **base64** para evitar erro de encoding no navegador. O cliente cola o token do BotFather e clica em Conectar.
3. **Enviar arquivo .txt** – O cliente salva o token em um arquivo (ex.: `token.txt`) e usa "Selecionar arquivo .txt". O conteúdo é lido e enviado em base64. Contorna qualquer problema de colar no navegador.
4. **API** – O backend aceita o token no header `X-Telegram-Bot-Token` ou no body como `bot_token_b64` (base64). Integrações podem usar isso.

**O que o administrador precisa configurar no servidor:**
- `TELEGRAM_WEBHOOK_BASE_URL` – URL pública do backend (ex.: `https://api.seudominio.com`). Em teste local, use ngrok: `ngrok http 8000` e coloque a URL HTTPS no `.env`.

Sem essa URL, o webhook não é registrado e o bot não recebe mensagens pelo dashboard.

---

## Modo simples (sem dashboard)

O chat do bot **também** pode rodar sem dashboard, com long polling:

1. Na pasta raiz do projeto: `python run_bot.py`
2. O bot usa `TELEGRAM_BOT_TOKEN` do `.env` e responde no Telegram.

Produção 24/7: `python run_production.py`
