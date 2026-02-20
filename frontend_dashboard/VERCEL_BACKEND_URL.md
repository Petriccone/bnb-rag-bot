# Configurar a API no dashboard (Vercel)

Para login, cadastro e Base de conhecimento funcionarem, o dashboard precisa saber a URL da API.

## Variáveis que o projeto usa

- **NEXT_PUBLIC_API_URL** — usada pelo código no navegador (build). Ex.: `https://bnb-rag-api.vercel.app`
- **BACKEND_URL** — usada pelo rewrite no Next (next.config.js) quando as chamadas passam pelo mesmo domínio.

Se você já tem **NEXT_PUBLIC_API_URL** e **BACKEND_URL** definidas (ex.: em "All Environments") com a URL da API, não precisa mudar nada. O cliente usa `NEXT_PUBLIC_API_URL` quando está disponível no build.

## Erro 405 ou "Não foi possível conectar"

- **405:** em geral a requisição está indo para o dashboard em vez da API. Confira se `NEXT_PUBLIC_API_URL` está definida para o ambiente em que você está fazendo o deploy (Production e/ou Preview) e se fez **Redeploy** depois de alterar variáveis.
- **Não foi possível conectar:** a URL da API pode estar errada ou a API pode estar fora do ar. Teste abrindo a URL da API no navegador.

## Resumo

| Variável                 | Uso |
|--------------------------|-----|
| NEXT_PUBLIC_API_URL      | Cliente (navegador) chama a API direto quando essa variável existe no build. |
| BACKEND_URL              | Rewrite no Next (next.config.js) encaminha `/api/*` para essa URL. |

Valor em ambos: URL do backend **sem** barra no final (ex.: `https://bnb-rag-api.vercel.app`). Marque os ambientes que você usa (Production / Preview) e faça **Redeploy** após alterar.
