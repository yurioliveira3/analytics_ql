-- Migração para adicionar soft delete nas tabelas de chat
-- Descrição: Adiciona colunas 'deleted' para implementar soft delete

-- Adiciona coluna deleted na tabela chat_sessions
ALTER TABLE metadata.chat_sessions 
ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- Adiciona coluna deleted na tabela chat_messages  
ALTER TABLE metadata.chat_messages 
ADD COLUMN deleted BOOLEAN NOT NULL DEFAULT FALSE;

-- Criar índices para melhorar performance das consultas com deleted = false
CREATE INDEX idx_chat_sessions_deleted ON metadata.chat_sessions(deleted) WHERE deleted = FALSE;
CREATE INDEX idx_chat_messages_deleted ON metadata.chat_messages(deleted) WHERE deleted = FALSE;

-- Comentários para documentação
COMMENT ON COLUMN metadata.chat_sessions.deleted IS 'Marca se a sessão foi deletada (soft delete)';
COMMENT ON COLUMN metadata.chat_messages.deleted IS 'Marca se a mensagem foi deletada (soft delete)';
