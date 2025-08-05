-- ====================================================================
-- Script de verificação do schema metadata
-- Execute este script após rodar o metadata.sql para verificar se tudo foi criado
-- ====================================================================

-- Verificar se o schema foi criado
SELECT schema_name 
FROM information_schema.schemata 
WHERE schema_name = 'metadata';

-- Verificar se as tabelas foram criadas
SELECT table_name, table_type
FROM information_schema.tables 
WHERE table_schema = 'metadata'
ORDER BY table_name;

-- Verificar se os índices foram criados
SELECT 
    schemaname,
    tablename,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'metadata'
ORDER BY tablename, indexname;

-- Verificar permissões do usuário frontend_user
SELECT 
    table_schema,
    table_name,
    privilege_type,
    is_grantable
FROM information_schema.table_privileges 
WHERE grantee = 'frontend_user' 
AND table_schema = 'metadata'
ORDER BY table_name, privilege_type;

-- Verificar permissões em sequências
SELECT 
    sequence_schema,
    sequence_name,
    privilege_type
FROM information_schema.usage_privileges 
WHERE grantee = 'frontend_user' 
AND object_schema = 'metadata'
ORDER BY sequence_name;

-- Testar inserção em chat_sessions (deve funcionar)
INSERT INTO metadata.chat_sessions (title) 
VALUES ('Teste de Conexão') 
RETURNING id, title, created_at;

-- Testar inserção em chat_messages (deve funcionar)
INSERT INTO metadata.chat_messages (session_id, role, content)
SELECT id, 'user', 'Teste de mensagem'
FROM metadata.chat_sessions 
WHERE title = 'Teste de Conexão'
RETURNING id, session_id, role, content, created_at;

-- Limpar dados de teste
DELETE FROM metadata.chat_sessions WHERE title = 'Teste de Conexão';

ECHO '✅ Verificação concluída! Se não houve erros, o schema está pronto para uso.';
