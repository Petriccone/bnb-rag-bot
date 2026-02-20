-- Adiciona base de conhecimento (namespace) por agente.
-- Cada agente pode ter seu próprio namespace = sua própria base de documentos.
-- Em documentos, use o mesmo embedding_namespace ao enviar arquivos para esse agente.

ALTER TABLE agents ADD COLUMN IF NOT EXISTS embedding_namespace TEXT;

COMMENT ON COLUMN agents.embedding_namespace IS 'Namespace da base de conhecimento deste agente (igual ao embedding_namespace dos documentos).';
