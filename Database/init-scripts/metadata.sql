-- ====================================================================
-- Script de criação do schema metadata para AnalyticSQL
-- Banco: analytics_db
-- Schema: metadata
-- ====================================================================

-- Criar schema metadata
CREATE SCHEMA IF NOT EXISTS metadata;

-- ====================================================================
-- Tabelas do sistema de histórico de chats
-- ====================================================================

-- Tabela de sessões de chat (nova estrutura)
CREATE TABLE metadata.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NULL, -- Futuro: integração com sistema de usuários
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    title TEXT NULL
);

-- Tabela de mensagens do chat (nova estrutura)
CREATE TABLE metadata.chat_messages (
    id BIGSERIAL PRIMARY KEY,
    session_id UUID NOT NULL REFERENCES metadata.chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    token_count INTEGER NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Campos específicos para mensagens do assistente
    generated_query TEXT NULL,
    explanation TEXT NULL,
    used_tables TEXT NULL, -- JSON string
    ml_algorithm VARCHAR(100) NULL,
    execution_result TEXT NULL, -- JSON string dos resultados
    execution_time_ms INTEGER NULL,
    total_cost VARCHAR(50) NULL,
    plan_rows INTEGER NULL,
    chart_type VARCHAR(50) NULL,
    insights TEXT NULL
);

-- Tabela legada (manter para compatibilidade)
CREATE TABLE metadata.chat_history (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(128) NOT NULL,
    user_question TEXT NOT NULL,
    generated_query TEXT NULL,
    execution_result TEXT NULL,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

-- Tabela de histórico de queries (manter existente)
CREATE TABLE metadata.query_history (
    id SERIAL PRIMARY KEY,
    query_text TEXT NOT NULL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    execution_time_ms INTEGER,
    plan_total_cost DECIMAL(10,2), 
    plan_rows INTEGER,
    db_user TEXT NOT NULL
);

-- ====================================================================
-- Índices para performance
-- ====================================================================

-- Índices para chat_sessions
CREATE INDEX ix_chat_sessions_created ON metadata.chat_sessions(created_at DESC);

-- Índices para chat_messages
CREATE INDEX ix_chat_messages_session_created ON metadata.chat_messages(session_id, created_at DESC);
CREATE INDEX ix_chat_messages_role ON metadata.chat_messages(role);
CREATE INDEX ix_chat_messages_created ON metadata.chat_messages(created_at DESC);

-- Índice para chat_history (legado)
CREATE INDEX idx_chat_history_session_id ON metadata.chat_history(session_id);

-- Índice para query_history
CREATE INDEX ix_query_history_executed ON metadata.query_history(executed_at DESC);

-- ====================================================================
-- Grants necessários para o usuário frontend_user
-- ====================================================================

GRANT USAGE ON SCHEMA metadata TO frontend_user;

-- Permissões para chat_sessions
GRANT SELECT, INSERT, UPDATE, DELETE ON metadata.chat_sessions TO frontend_user;

-- Permissões para chat_messages  
GRANT SELECT, INSERT, UPDATE, DELETE ON metadata.chat_messages TO frontend_user;
GRANT USAGE, SELECT ON SEQUENCE metadata.chat_messages_id_seq TO frontend_user;

-- Permissões para chat_history (legado)
GRANT SELECT, INSERT, UPDATE, DELETE ON metadata.chat_history TO frontend_user;
GRANT USAGE, SELECT ON SEQUENCE metadata.chat_history_id_seq TO frontend_user;

-- Permissões para query_history
GRANT SELECT, INSERT ON metadata.query_history TO frontend_user;
GRANT USAGE, SELECT ON SEQUENCE metadata.query_history_id_seq TO frontend_user;