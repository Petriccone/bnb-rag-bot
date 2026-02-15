-- Base de conhecimento: chunks com embeddings para RAG.
-- Requer extensão pgvector (no Supabase: Database → Extensions → vector).
-- Dimensão 1536 = OpenAI text-embedding-3-small.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    chunk_index INT NOT NULL,
    content TEXT NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_document_chunks_tenant ON document_chunks (tenant_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document ON document_chunks (document_id);

-- Índice HNSW para busca por similaridade (cosine). Cria após ter dados.
-- CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks
--   USING hnsw (embedding vector_cosine_ops);

COMMENT ON TABLE document_chunks IS 'Chunks de documentos da base de conhecimento por tenant; embedding OpenAI 1536 dims.';
