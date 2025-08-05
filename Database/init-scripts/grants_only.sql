-- ====================================================================
-- Grants necessários para o usuário frontend_user no schema metadata
-- Execute este script se precisar aplicar apenas as permissões
-- ====================================================================

-- Conceder uso do schema
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

-- Verificar se as permissões foram aplicadas
SELECT 
    table_schema,
    table_name,
    privilege_type,
    grantee
FROM information_schema.table_privileges 
WHERE grantee = 'frontend_user' 
AND table_schema = 'metadata'
ORDER BY table_name, privilege_type;
