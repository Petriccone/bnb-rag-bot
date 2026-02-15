# Sandbox / Staging: testar sem atualizar o site oficial

Você pode trabalhar como se o app já estivesse no ar com clientes: desenvolve e testa em um ambiente separado e só sobe para o site oficial quando estiver pronto.

## Ideia geral

- **Site oficial (produção):** atualiza **só** quando você faz merge para o branch de produção (ex.: `main`) e o Vercel faz o deploy desse branch.
- **Sandbox (staging/preview):** você faz push em outro branch (ex.: `develop`); o Vercel gera uma **Preview** com URL própria. Pode fazer deploy à vontade; o oficial não muda.

---

## Opção 1: Usar branches + Preview da Vercel (recomendado)

Não precisa criar outro projeto. Só usar dois branches.

### Configuração

1. **Branch de produção:** no projeto do dashboard na Vercel, em **Settings → Git**, o **Production Branch** costuma ser `main`. Deixe assim.
2. **Branch de sandbox:** crie e use um branch para o dia a dia, por exemplo `develop` ou `staging`:
   ```bash
   git checkout -b develop
   git push -u origin develop
   ```
3. **Fluxo de trabalho:**
   - Trabalhe sempre em `develop` (novas features, correções, testes).
   - Dê push em `develop` quando quiser. A Vercel faz um **Preview Deployment** e mostra uma URL tipo:
     - `bnb-rag-bot-git-develop-seu-usuario.vercel.app`
   - Use essa URL para testar como se fosse o app “ao vivo”, com clientes.
   - Quando estiver tudo certo, faça **merge** de `develop` em `main`:
     ```bash
     git checkout main
     git pull origin main
     git merge develop
     git push origin main
     ```
   - Só aí o **site oficial** é atualizado.

### Onde ver a URL do Preview

- No repositório (GitHub/GitLab): cada push em `develop` pode gerar um comentário no commit/PR com o link do preview.
- Na Vercel: **Deployments** → clique no deploy do branch `develop` → a URL do preview aparece no topo.

### Variáveis de ambiente no Preview

Em **Settings → Environment Variables**, ao criar/editar uma variável, marque também **Preview** (além de Production) se quiser que o sandbox use a mesma API. Assim tanto produção quanto preview usam, por exemplo, `NEXT_PUBLIC_API_URL` apontando para a API.

---

## Opção 2: Dois projetos na Vercel (staging com URL fixa)

Se quiser uma URL **fixa** para o sandbox (ex.: `bnb-rag-staging.vercel.app`) em vez da URL de preview que muda a cada deploy:

1. Na Vercel, crie um **novo projeto** (ex.: “B&B RAG Dashboard – Staging”).
2. Conecte ao **mesmo repositório**, mas escolha o branch **`develop`** (ou o branch que você usar de sandbox).
3. Configure as variáveis (ex.: `NEXT_PUBLIC_API_URL`) nesse projeto de staging.
4. A partir daí:
   - **Produção:** projeto original, branch `main` → site oficial.
   - **Staging:** novo projeto, branch `develop` → URL fixa do sandbox; pode fazer deploy à vontade.

Assim o “app funcional com clientes” que você testa é o staging; o oficial só muda quando você sobe para `main` no projeto de produção.

---

## Resumo

| Onde você mexe | O que acontece |
|----------------|-----------------|
| Trabalha e dá push em `develop` | Só o sandbox/preview atualiza (URL de preview ou projeto de staging). |
| Faz merge de `develop` em `main` e push | O site oficial (produção) atualiza. |

Dessa forma você cria e testa tudo antes de subir o deploy oficial.
