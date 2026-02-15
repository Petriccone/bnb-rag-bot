# Base de conhecimento (documentos + RAG)

## O que é

A base de conhecimento permite que o bot use **documentos enviados no dashboard** para responder com contexto (RAG). Cada tenant tem seus próprios documentos; o isolamento é por `tenant_id`.

## Como ativar

1. **Banco (pgvector)**  
   No Supabase (ou Postgres), rode o schema que cria a extensão e a tabela de chunks:
   ```bash
   psql $DATABASE_URL -f database/schema_pgvector.sql
   ```
   No Supabase: Database → SQL Editor → colar o conteúdo de `database/schema_pgvector.sql` e executar.

2. **OpenAI para embeddings**  
   No `.env` (e na Vercel, nas variáveis de ambiente), defina:
   ```env
   OPENAI_API_KEY=sk-...
   ```
   Opcional: `OPENAI_EMBEDDING_MODEL=text-embedding-3-small` (padrão, 1536 dimensões).

3. **Upload no dashboard**  
   Em **Base de conhecimento**, envie arquivos **PDF**, **TXT**, **Excel** (.xlsx, .xls) ou **imagens** (PNG, JPG/JPEG). São salvos, o texto é extraído (em imagens via OpenAI Vision), dividido em trechos (chunks), transformado em embeddings e gravado em `document_chunks`. O bot usa esses trechos na resposta.

## Fluxo

- **Upload:** o backend salva o arquivo, insere em `documents` e chama o ingest (extração de texto → chunk → embedding → insert em `document_chunks`). Formatos processados: .pdf, .txt, .xlsx, .xls, .png, .jpg, .jpeg. Imagens usam OpenAI Vision para gerar descrição textual.
- **Resposta do bot:** quando o tenant **não** tem pasta do Google Drive configurada, o `agent_facade` usa a busca vetorial por tenant (`knowledge_rag.search_document_chunks`). O texto da mensagem do lead é convertido em embedding e comparado aos chunks; os mais similares viram contexto para o LLM.
- **Prioridade de contexto:** 1) Pasta do Drive do tenant (`settings.drive_folder_id`), 2) variável global `DRIVE_FOLDER_ID`, 3) base de conhecimento (document_chunks), 4) mensagem de “não configurado”.

## Deletar documento

Ao remover um documento na tela, o backend apaga os chunks correspondentes em `document_chunks` e o arquivo em disco.

## Dependências

- `openai` e `pypdf` no backend (já em `platform_backend/requirements.txt`).
- Postgres com extensão `vector` (pgvector).
