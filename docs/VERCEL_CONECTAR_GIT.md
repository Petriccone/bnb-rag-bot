# Conectar o projeto à Vercel (URL do repositório)

Repositório deste projeto: **https://github.com/Petriccone/bnb-rag-bot**

Use essa URL na Vercel quando pedir o repositório Git. Autorize o acesso ao GitHub e siga [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md) para configurar os dois projetos (API e Dashboard).

---

A Vercel pede a **URL do repositório Git** para fazer o deploy. Você precisa ter o código em um repositório no **GitHub**, **GitLab** ou **Bitbucket**.

---

## Se você ainda **não** tem o projeto no GitHub

### 1. Criar o repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login.
2. Clique em **“+”** (canto superior direito) → **“New repository”**.
3. Dê um nome (ex.: `bbrag` ou `bnb-rag`).
4. Deixe **público** ou privado, como preferir.
5. **Não** marque “Add a README” (o projeto já tem arquivos).
6. Clique em **“Create repository”**.

### 2. Inicializar Git no seu PC e enviar o código

No terminal, na pasta do projeto (ex.: `c:\Users\rsp88\B&B RAG`):

```powershell
# Inicializar Git (se ainda não tiver)
git init

# Adicionar todos os arquivos
git add .

# Primeiro commit
git commit -m "Projeto B&B RAG - deploy Vercel"

# Trocar "SEU_USUARIO" e "NOME_DO_REPO" pela URL que o GitHub mostrou
# Ex.: se o repo for github.com/joao/bbrag, use:
#   git remote add origin https://github.com/joao/bbrag.git
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git

# Enviar para o GitHub (branch main)
git branch -M main
git push -u origin main
```

A **URL do repositório** que a Vercel pede é essa mesma, por exemplo:

- `https://github.com/SEU_USUARIO/NOME_DO_REPO`

ou, no botão verde **“Code”** do GitHub, a URL que aparece em **“HTTPS”**.

---

## Se o projeto **já** está no GitHub

1. Abra o repositório no GitHub no navegador.
2. Clique no botão verde **“Code”**.
3. Copie a URL em **HTTPS** (ex.: `https://github.com/usuario/bbrag.git`).
4. Na Vercel, quando pedir a URL do repositório, cole essa URL (pode ser com ou sem `.git` no final).

---

## Depois de colar a URL na Vercel

- A Vercel vai pedir permissão para acessar sua conta GitHub (autorize).
- Em seguida você configura os **dois projetos** como em [DEPLOY_VERCEL.md](DEPLOY_VERCEL.md):
  - **Projeto 1 (API):** Root em branco.
  - **Projeto 2 (Dashboard):** Root = `frontend_dashboard`.
- E define as variáveis de ambiente de cada um.

Resumo: a URL que a Vercel pede é a **URL do repositório no GitHub** (ou GitLab/Bitbucket), por exemplo `https://github.com/seu-usuario/nome-do-repo`.
