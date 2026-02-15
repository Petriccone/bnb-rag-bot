# Configurar a API no dashboard (Vercel)

Para login, cadastro e **upload na Base de conhecimento** funcionarem em produção, o frontend precisa saber a URL da API.

## Erro 405 no upload (/documents)

Se ao enviar um arquivo em **Base de conhecimento** aparecer **405** ou "Failed to load resource: 405", o navegador está mandando o POST para o próprio dashboard em vez da API. A solução é configurar `NEXT_PUBLIC_API_URL` no projeto do dashboard na Vercel (abaixo) e fazer **Redeploy**.

---

## Opção recomendada (evita 405 no cadastro e no upload)

Chamada **direta** do navegador para a API (o backend já tem CORS liberado).

1. Abra a [Vercel](https://vercel.com) e entre no projeto do **dashboard** (Root = `frontend_dashboard`).

2. **Settings** → **Environment Variables**.

3. Adicione:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://bnb-rag-api.vercel.app`  
   **Importante:** sem barra no final, sem `/api`. Ex.: `https://bnb-rag-api.vercel.app` (não `https://bnb-rag-api.vercel.app/`).  
   Use a URL do seu projeto da API se for diferente.

4. Marque **Production** (e Preview se quiser) e salve.

5. **Deployments** → **Redeploy** (para o build pegar a variável).

Com isso, o cadastro/login passa a funcionar (o navegador chama a API diretamente).

---

## Opção alternativa (proxy pelo Next.js)

Se preferir que as chamadas passem pelo mesmo domínio do dashboard:

- **Name:** `BACKEND_URL`  
- **Value:** `https://bnb-rag-api.vercel.app`  
- Depois do primeiro deploy com essa variável, faça **Redeploy** para o rewrite ser aplicado.
