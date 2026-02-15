# Upload de documentos (multi-tenant)

## Objetivo
Cada tenant pode enviar sua base de conhecimento (documentos) com namespace vetorial isolado.

## Regras
- Todo documento deve ter `tenant_id` e `embedding_namespace` (ex.: tenant_id + agent_id ou apenas tenant_id).
- Nenhum documento de um tenant pode ser acessado por outro tenant.
- Armazenar em `documents`: file_path (ou URL), embedding_namespace.
- O RAG/Drive por tenant pode usar `settings.drive_folder_id` do tenant ou arquivos enviados pela plataforma; o namespace garante isolamento em buscas vetoriais.

## Fluxo
1. Validar tenant_id e arquivo.
2. Gerar ou receber embedding_namespace (ex.: f"tenant_{tenant_id}").
3. Inserir em `documents` (tenant_id, file_path, embedding_namespace).
4. Processar arquivo para índice vetorial: feito em `execution/document_ingest.py` (extração de texto, chunk, embedding OpenAI, insert em `document_chunks`). Chamado pelo backend após upload de .pdf ou .txt. Ver `docs/BASE_DE_CONHECIMENTO.md`.
