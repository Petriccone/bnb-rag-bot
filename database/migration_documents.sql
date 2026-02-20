-- Migration: Adicionar campos à tabela documents para suporte a Excel, URLs e status
-- Execute este script se já tem a tabela documents criada

-- Adicionar colunas se não existirem
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_name TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_size_mb REAL DEFAULT 0;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS file_type TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS source_url TEXT;
ALTER TABLE documents ADD COLUMN IF NOT EXISTS status TEXT DEFAULT 'pending';

-- Atualizar registros existentes com valores padrão
UPDATE documents SET file_name = COALESCE(file_name, 'unknown'), 
                     file_size_mb = COALESCE(file_size_mb, 0),
                     file_type = COALESCE(file_type, 'unknown'),
                     status = COALESCE(status, 'completed')
WHERE file_name IS NULL OR file_size_mb IS NULL OR file_type IS NULL OR status IS NULL;

-- Criar índice para status
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents (status);
