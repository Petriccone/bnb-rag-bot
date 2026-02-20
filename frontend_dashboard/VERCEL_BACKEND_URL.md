# Configurar a API no dashboard (Vercel)

O dashboard chama **sempre** o próprio domínio (`/api/*`). O Next.js encaminha para o backend via **rewrite** (next.config.js). Assim o **405 no login/cadastro** some: a requisição não depende de variável no build do cliente.

## Uma variável: BACKEND_URL

1. Projeto do **dashboard** na Vercel → **Settings** → **Environment Variables**.
2. **Name:** `BACKEND_URL`  
   **Value:** `https://bnb-rag-api.vercel.app` (URL da API, sem barra no final).
3. Marque **Production** (e **Preview** se usar).
4. **Save** → **Deployments** → **Redeploy** (para o rewrite usar a nova variável).

Não é obrigatório ter `NEXT_PUBLIC_API_URL`: o cliente usa o mesmo domínio do dashboard; o rewrite usa `BACKEND_URL`.

## Erro 405 ou "Não foi possível conectar"

- **405:** o rewrite não está apontando para o backend (falta `BACKEND_URL` no build ou valor errado). Defina `BACKEND_URL` e faça **Redeploy**.
- **Não foi possível conectar:** URL do backend errada ou API fora do ar. Confira `BACKEND_URL` e se a API responde (abrir a URL no navegador).
