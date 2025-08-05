-- 1. Cria o novo user (role) com uma senha segura.
CREATE ROLE frontend_user WITH LOGIN PASSWORD 'senha_forte'; -- Substitua a senha por uma senha forte e segura.

-- 2. Permite que o novo usuário se conecte ao seu banco de dados.
GRANT CONNECT ON DATABASE analytics_db TO frontend_user;

-- 3. Concede permissão de uso no schema 'public'.
GRANT USAGE ON SCHEMA public TO frontend_user;
GRANT USAGE ON SCHEMA lang TO frontend_user;
GRANT USAGE ON SCHEMA alunos TO frontend_user;
GRANT USAGE ON SCHEMA produtos TO frontend_user;

-- 4. Concede permissão de LEITURA (SELECT) em TODAS as tabelas existentes no schema.
GRANT SELECT ON ALL TABLES IN SCHEMA public TO frontend_user;
GRANT SELECT ON ALL TABLES IN SCHEMA lang TO frontend_user;
GRANT SELECT ON ALL TABLES IN SCHEMA alunos TO frontend_user;
GRANT SELECT ON ALL TABLES IN SCHEMA produtos TO frontend_user;

-- 5. (Recomendado) Garante que o usuário terá permissão de LEITURA
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO frontend_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA lang GRANT SELECT ON TABLES TO frontend_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA alunos GRANT SELECT ON TABLES TO frontend_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA produtos GRANT SELECT ON TABLES TO frontend_user;