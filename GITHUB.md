# Como subir o projeto no GitHub

## 1. Criar o repositório no GitHub

1. Acesse [github.com](https://github.com) e faça login.
2. Clique em **"+"** (canto superior direito) → **New repository**.
3. Escolha um nome (ex.: `bnb-rag-bot` ou `sdr-telegram-filtros`).
4. Deixe **Private** se não quiser que o código fique público (recomendado — o projeto tem lógica de negócio).
5. **Não** marque "Add a README" (você já tem um). Clique em **Create repository**.

---

## 2. No seu computador (pasta do projeto)

Abra o terminal na pasta do projeto (`B&B RAG`) e rode na ordem:

```powershell
cd "c:\Users\rsp88\B&B RAG"

# Inicializar o Git (se ainda não tiver)
git init

# Adicionar todos os arquivos (o .gitignore já evita .env, token.json, credentials.json)
git add .

# Primeiro commit
git commit -m "Bot SDR Telegram - filtros de água (SPIN + RAG Drive)"

# Conectar ao repositório que você criou (troque SEU_USUARIO e NOME_DO_REPO pelo seu)
git remote add origin https://github.com/SEU_USUARIO/NOME_DO_REPO.git

# Enviar para o GitHub (branch main)
git branch -M main
git push -u origin main
```

**Troque** `SEU_USUARIO` e `NOME_DO_REPO` pelo seu usuário do GitHub e o nome do repositório.  
Exemplo: se o repositório for `https://github.com/joao/bnb-rag-bot`, use:

```powershell
git remote add origin https://github.com/joao/bnb-rag-bot.git
```

---

## 3. O que não sobe (protegido pelo .gitignore)

- `.env` (tokens e senhas)
- `token.json` e `credentials.json` (Google)
- `.tmp/` (banco SQLite, cache, logs)
- `__pycache__/`, `venv/`

Assim você não expõe segredos no GitHub.

---

## 4. Depois do primeiro push

- Para enviar novas alterações:
  ```powershell
  git add .
  git commit -m "Descrição do que mudou"
  git push
  ```
- Para conectar ao **Railway**: no Railway, use **Deploy from GitHub** e escolha esse repositório.
