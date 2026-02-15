# Como Contribuir com o B&B RAG Bot

Primeiramente, muito obrigado pelo seu interesse em contribuir! 🎉

Adoramos receber ajuda da comunidade e ficamos felizes em ter você aqui. Qualquer contribuição, desde a correção de um simples erro de digitação até a implementação de uma nova funcionalidade complexa, é muito bem-vinda.

Este documento é um guia com as diretrizes para contribuir com o projeto.

## Código de Conduta

Este projeto e todos que participam dele são regidos pelo nosso `CODE_OF_CONDUCT.md`. Ao participar, você concorda em seguir seus termos.

## Como Posso Ajudar?

Existem várias formas de contribuir, e nem todas envolvem escrever código.

*   **Reportar Bugs:** Se você encontrar um comportamento inesperado, por favor, abra uma [issue](https://github.com/Petriccone/bnb-rag-bot/issues) descrevendo o problema em detalhes.
*   **Sugerir Melhorias:** Tem uma ideia para uma nova funcionalidade ou uma melhoria em algo que já existe? Abra uma [issue](https://github.com/Petriccone/bnb-rag-bot/issues) para discutirmos.
*   **Melhorar a Documentação:** Encontrou algo na documentação que está confuso, incompleto ou errado? Sugira uma alteração!
*   **Escrever Código:** Pegue uma issue aberta (especialmente as com a tag `good first issue` ou `help wanted`) e envie um Pull Request com a solução.

## Começando a Desenvolver

Para fazer alterações no código, você precisará configurar o ambiente de desenvolvimento na sua máquina.

1.  **Faça um Fork** do repositório clicando no botão "Fork" no canto superior direito da página do GitHub.

2.  **Clone o seu fork** para a sua máquina:
    ```bash
    git clone https://github.com/SEU-USUARIO/bnb-rag-bot.git
    cd bnb-rag-bot
    ```

3.  **Crie um Ambiente Virtual** e instale as dependências. Recomendamos o uso de `venv`:
    ```bash
    python -m venv venv
    source venv/bin/activate  # No Windows: venv\Scripts\activate
    ```

4.  **Instale as dependências** do projeto:
    ```bash
    pip install -r requirements.txt
    ```

5.  **Configure suas variáveis de ambiente**. Copie o arquivo de exemplo e preencha com suas chaves. Para desenvolvimento, você só precisa do Telegram e do OpenRouter.
    ```bash
    cp .env.example .env
    ```
    Agora, edite o arquivo `.env` com suas informações.

6.  **Crie uma nova branch** para a sua funcionalidade ou correção:
    ```bash
    git checkout -b nome-da-sua-feature-ou-fix
    ```

7.  **Faça suas alterações!** Codifique, teste e se divirta.

## Enviando um Pull Request (PR)

Depois de fazer suas alterações na sua branch, você está pronto para enviá-las para o projeto principal.

1.  **Faça o commit** das suas alterações com uma mensagem clara:
    ```bash
    git add .
    git commit -m "feat: Adiciona nova funcionalidade X"
    # ou "fix: Corrige o bug Y"
    # ou "docs: Melhora a documentação sobre Z"
    ```

2.  **Envie sua branch** para o seu fork no GitHub:
    ```bash
    git push origin nome-da-sua-feature-ou-fix
    ```

3.  **Abra um Pull Request:** Vá para a página do repositório original no GitHub. Um banner aparecerá sugerindo a criação de um Pull Request a partir da sua nova branch. Clique nele.

4.  **Descreva seu PR:** Dê um título claro e uma descrição do que você fez. Se o seu PR resolve uma issue existente, mencione-a na descrição usando `Resolve #123`.

Pronto! Agora é só aguardar a revisão. Faremos o nosso melhor para analisar o seu PR o mais rápido possível.

Mais uma vez, obrigado por ajudar a tornar este projeto ainda melhor!
