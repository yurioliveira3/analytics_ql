"""
Script simples para criar as tabelas de chat.
"""

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
import os

# Carrega variáveis de ambiente
load_dotenv(os.path.join(os.path.dirname(__file__), 'App', '.env'))

# String de conexão
CONNECTION_STRING = os.getenv(
    'PG_CONNECTION_STRING', 
    'postgresql://localhost:5432/analytics_db'
)

print(f"🔌 Conectando ao banco: {CONNECTION_STRING.split('@')[0]}@...")

# Conecta ao banco
engine = create_engine(CONNECTION_STRING)

# SQL para criar schema (opcional se não tiver permissão)
create_schema_sql = "CREATE SCHEMA IF NOT EXISTS metadata;"

# SQL para criar tabelas (usando public se metadata não existir)
create_tables_sql = """
-- Verificar se schema metadata existe, senão usar public
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.schemata WHERE schema_name = 'metadata') THEN
        -- Usar schema public
        CREATE TABLE IF NOT EXISTS public.chat_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            title TEXT
        );

        CREATE TABLE IF NOT EXISTS public.chat_messages (
            id BIGSERIAL PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES public.chat_sessions(id) ON DELETE CASCADE,
            role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            token_count INTEGER,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            generated_query TEXT,
            explanation TEXT,
            used_tables TEXT,
            ml_algorithm VARCHAR(100),
            execution_result TEXT,
            execution_time_ms INTEGER,
            total_cost VARCHAR(50),
            plan_rows INTEGER,
            chart_type VARCHAR(50),
            insights TEXT
        );

        -- Índices para schema public
        CREATE INDEX IF NOT EXISTS ix_chat_messages_session_created 
        ON public.chat_messages(session_id, created_at DESC);

        CREATE INDEX IF NOT EXISTS ix_chat_sessions_created 
        ON public.chat_sessions(created_at DESC);

        CREATE INDEX IF NOT EXISTS ix_chat_messages_role 
        ON public.chat_messages(role);
    ELSE
        -- Usar schema metadata
        CREATE TABLE IF NOT EXISTS metadata.chat_sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            user_id UUID,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            title TEXT
        );

        CREATE TABLE IF NOT EXISTS metadata.chat_messages (
            id BIGSERIAL PRIMARY KEY,
            session_id UUID NOT NULL REFERENCES metadata.chat_sessions(id) ON DELETE CASCADE,
            role VARCHAR(10) NOT NULL CHECK (role IN ('user', 'assistant')),
            content TEXT NOT NULL,
            token_count INTEGER,
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
            generated_query TEXT,
            explanation TEXT,
            used_tables TEXT,
            ml_algorithm VARCHAR(100),
            execution_result TEXT,
            execution_time_ms INTEGER,
            total_cost VARCHAR(50),
            plan_rows INTEGER,
            chart_type VARCHAR(50),
            insights TEXT
        );

        -- Índices para schema metadata
        CREATE INDEX IF NOT EXISTS ix_chat_messages_session_created 
        ON metadata.chat_messages(session_id, created_at DESC);

        CREATE INDEX IF NOT EXISTS ix_chat_sessions_created 
        ON metadata.chat_sessions(created_at DESC);

        CREATE INDEX IF NOT EXISTS ix_chat_messages_role 
        ON metadata.chat_messages(role);
    END IF;
END $$;
"""

def main():
    print("🔄 Criando tabelas de chat...")
    
    try:
        with engine.connect() as conn:
            # Tenta criar schema primeiro
            try:
                print("📁 Tentando criar schema metadata...")
                conn.execute(text(create_schema_sql))
                print("✅ Schema metadata criado ou já existe")
            except Exception as e:
                print(f"⚠️  Não foi possível criar schema metadata: {e}")
                print("📁 Continuando com schema public...")
            
            # Cria tabelas
            print("📋 Criando tabelas e índices...")
            conn.execute(text(create_tables_sql))
            
            conn.commit()
            
        print("✅ Tabelas criadas com sucesso!")
        
        # Verifica se as tabelas foram criadas
        with engine.connect() as conn:
            # Verifica em ambos os schemas
            for schema in ['metadata', 'public']:
                try:
                    result = conn.execute(text(f"""
                        SELECT table_name 
                        FROM information_schema.tables 
                        WHERE table_schema = '{schema}' 
                        AND table_name LIKE 'chat_%'
                        ORDER BY table_name
                    """))
                    
                    tables = [row[0] for row in result]
                    if tables:
                        print(f"📊 Tabelas encontradas no schema {schema}: {tables}")
                        
                        # Verifica a tabela chat_history se existir
                        if schema == 'metadata':
                            history_result = conn.execute(text(f"""
                                SELECT COUNT(*) 
                                FROM information_schema.tables 
                                WHERE table_schema = '{schema}' 
                                AND table_name = 'chat_history'
                            """))
                            
                            if history_result.scalar() > 0:
                                print(f"📜 Tabela chat_history encontrada no schema {schema}")
                
                except Exception as e:
                    print(f"⚠️  Erro ao verificar schema {schema}: {e}")
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
