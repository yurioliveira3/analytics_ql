-- Extensão obrigatória para embeddings vetoriais
CREATE EXTENSION IF NOT EXISTS "vector";

-- Cria o schema para as tabelas do LangChain
CREATE SCHEMA IF NOT EXISTS lang;

-- ATENÇÃO: Os comandos DROP abaixo limpam as tabelas em cada reinicialização.
-- Remova ou comente em um ambiente de produção.
DROP TABLE IF EXISTS lang.langchain_pg_embedding;
DROP TABLE IF EXISTS lang.langchain_pg_collection;

-- Tabela para armazenar as "collections" (conjuntos de documentos)
CREATE TABLE lang.langchain_pg_collection (
    uuid UUID PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    cmetadata JSONB
);

COMMENT ON TABLE lang.langchain_pg_collection IS 'Tabela para agrupar embeddings em coleções, similar a índices.';

-- Tabela para armazenar os embeddings (vetores) e os documentos associados
CREATE TABLE lang.langchain_pg_embedding (
    id SERIAL PRIMARY KEY,
    uuid UUID NOT NULL,
    -- CORREÇÃO: Adicionado o schema 'lang' na referência da FK
    collection_id UUID NOT NULL REFERENCES lang.langchain_pg_collection(uuid) ON DELETE CASCADE,
    embedding VECTOR(1024),  -- ATENÇÃO: ajuste a dimensão (ex: 1536 para text-embedding-ada-002 da OpenAI)
    document TEXT,
    cmetadata JSONB,
    custom_id TEXT
);

COMMENT ON TABLE lang.langchain_pg_embedding IS 'Armazena os vetores de embedding, o texto original e metadados.';

-- Restrições para garantir integridade dos dados
ALTER TABLE lang.langchain_pg_embedding 
    ADD CONSTRAINT chk_dims_1024 CHECK (vector_dims(embedding)=1024);

-- Índice para acelerar a busca pelo collection_id
CREATE INDEX IF NOT EXISTS idx_langchain_pg_embedding_collection_id ON lang.langchain_pg_embedding (collection_id);

-- IMPORTANTE: Para buscas vetoriais rápidas, um índice de similaridade é essencial.
-- Ele deve ser criado DEPOIS que a tabela tiver um volume considerável de dados.
-- Deixei comentado como um exemplo para você executar manualmente.
/*
CREATE INDEX ON lang.langchain_pg_embedding USING ivfflat (embedding vector_l2_ops)
WITH (lists = 100);
*/

CREATE EXTENSION IF NOT EXISTS vector;
ALTER EXTENSION vector UPDATE;  -- se estiver desatualizada


ALTER TABLE lang.langchain_pg_embedding
  ALTER COLUMN embedding TYPE vector(1024)
  USING embedding::vector;

DROP INDEX IF EXISTS lang.idx_langchain_pg_embedding_embedding_cos;
CREATE INDEX idx_langchain_pg_embedding_embedding_cos
  ON lang.langchain_pg_embedding
  USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 100);
ANALYZE lang.langchain_pg_embedding;
