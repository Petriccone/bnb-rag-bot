# B&B RAG Bot - Agente de Vendas para Telegram

Este é um bot consultivo de vendas para Telegram, pronto para ser adaptado para qualquer produto ou serviço. Ele vem equipado com uma estrutura de IA de ponta para guiar usuários desde o primeiro contato até o pós-venda.

✨ **[Veja o vídeo de demonstração!](https://youtube.com)** 

## 🚀 Rode em 5 Minutos (Modo Básico)

Siga estes passos para ter a versão de texto do bot funcionando localmente.

1.  **Clone o repositório:**
    ```bash
    git clone https://github.com/Petriccone/bnb-rag-bot.git
    cd bnb-rag-bot
    ```

2.  **Instale as dependências:**
    ```bash
    # Recomendado: crie um ambiente virtual primeiro
    # python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    ```

3.  **Configure o ambiente:**
    Copie o arquivo de exemplo e preencha SÓ as duas primeiras variáveis.
    ```bash
    cp .env.example .env
    ```
    Edite o `.env`:
    - `TELEGRAM_BOT_TOKEN`: Obtenha com o [@BotFather](https://t.me/BotFather) no Telegram.
    - `OPENROUTER_API_KEY`: Obtenha em [openrouter.ai](https://openrouter.ai).

4.  **Rode o bot:**
    ```bash
    python run_bot.py
    ```

Pronto! Abra uma conversa com seu bot no Telegram e envie `/start` para começar.

---

## ✨ Funcionalidades

*   **🧠 Metodologia SPIN Selling**: Guia a conversa através dos estágios de **S**ituação, **P**roblema, **I**mplicação e **N**ecessidade de solução.
*   **🗣️ Suporte a Áudio**: Transcreve mensagens de voz do usuário (STT) e responde com áudio (TTS).
*   **📚 Base de Conhecimento com RAG**: Conecta-se a uma pasta no Google Drive para responder perguntas com base nos seus documentos (PDFs, Docs, etc).
*   **🗂️ Gestão de Estado**: Mantém o contexto da conversa, sabendo em que ponto da jornada de compra o usuário está.
*   **🖼️ Envio de Mídia**: Pode enviar imagens de produtos durante a fase de oferta.
*   **☁️ Pronto para Deploy**: Otimizado para rodar 24/7 em plataformas como Railway, Render e Fly.io.

## ⚙️ Configuração Avançada

Quer usar todo o poder do bot? Configure os módulos opcionais no seu arquivo `.env`.

*   **Para usar RAG (Google Drive):**
    - Siga o guia para criar suas credenciais no Google Cloud.
    - Adicione a `DRIVE_FOLDER_ID` da sua pasta de materiais no `.env`.

*   **Para usar Áudio (STT/TTS):**
    - Adicione sua `OPENAI_API_KEY` no `.env`.

*   **Para usar um Banco de Dados Persistente (Supabase):**
    - Adicione `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` no `.env`.
    - Execute o script `execution/supabase_schema.sql` no seu projeto Supabase.
    - Se não configurar, o bot usará um arquivo SQLite local (`.tmp/sdr_bot.db`).

*   **Para usar Buffer de Mensagens (Debounce):**
    - Adicione sua `REDIS_URL` no `.env` para agrupar múltiplas mensagens de texto em uma única resposta, economizando chamadas de API.

A documentação detalhada para cada uma dessas configurações está na seção **Guias de Deploy e Configuração**.

## 🤝 Contribuição e Comunidade

Este é um projeto de código aberto e adoramos receber ajuda! 

*   📜 **Código de Conduta**: Seja respeitoso e construtivo. Leia nosso [Código de Conduta](CODE_OF_CONDUCT.md).
*   🛠️ **Guia de Contribuição**: Quer reportar um bug ou adicionar uma funcionalidade? Veja como em nosso [Guia de Contribuição](CONTRIBUTING.md).

## 📚 Guias de Deploy e Configuração

*   **[DEPLOY.md](DEPLOY.md)**: Guia completo para colocar seu bot em produção (Railway, Render, Fly.io, etc).
*   **[TELEGRAM_COMO_RODAR.md](TELEGRAM_COMO_RODAR.md)**: Passos detalhados sobre o Telegram.
*   **Diretivas**: Altere o comportamento do agente (personalidade, fluxo, etc) editando os arquivos na pasta `directives/`.

## 🏗️ Arquitetura Resumida

- **Camada 1 — Diretivas**: SOPs em `directives/` (personalidade, SPIN, RAG, etc).
- **Camada 2 — Orquestração**: Lógica principal que aplica estados e chama os serviços.
- **Camada 3 — Execução**: Scripts em `execution/` (Telegram, STT, TTS, RAG, etc).
