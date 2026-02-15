# Configurar a API no dashboard (Vercel)

Para login e cadastro funcionarem em produção, o frontend precisa saber a URL da API.

## Opção recomendada (evita 405 no cadastro)

Chamada **direta** do navegador para a API (o backend já tem CORS liberado).

1. Abra a [Vercel](https://vercel.com) e entre no projeto do **dashboard** (Root = `frontend_dashboard`).

2. **Settings** → **Environment Variables**.

3. Adicione:
   - **Name:** `NEXT_PUBLIC_API_URL`
   - **Value:** `https://bnb-rag-api.vercel.app`  
   (sem `/api` no final; use a URL do seu projeto da API se for diferente.)

4. Marque **Production** (e Preview se quiser) e salve.

5. **Deployments** → **Redeploy** (para o build pegar a variável).

Com isso, o cadastro/login passa a funcionar (o navegador chama a API diretamente).

---

## Opção alternativa (proxy pelo Next.js)

Se preferir que as chamadas passem pelo mesmo domínio do dashboard:

- **Name:** `BACKEND_URL`  
- **Value:** `https://bnb-rag-api.vercel.app`  
- Depois do primeiro deploy com essa variável, faça **Redeploy** para o rewrite ser aplicado.
