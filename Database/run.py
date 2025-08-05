"""
Script de inicialização da aplicação com migração automática.
"""
import subprocess
import sys
import os

# Adiciona o diretório pai ao path para importar utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from App.utils.logger import get_logger

# Logger para este módulo
logger = get_logger(__name__)

def run_migration():
    """Executa as migrações do banco de dados."""
    logger.info("Executando migrações do banco de dados...")
    
    migration_script = os.path.join(
        os.path.dirname(__file__), 
        "Database", 
        "migrations", 
        "001_create_chat_tables.py"
    )
    
    try:
        result = subprocess.run([sys.executable, migration_script], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Migrações executadas com sucesso!")
            if result.stdout:
                logger.info(result.stdout)
        else:
            logger.error("Erro durante as migrações:")
            logger.error(result.stderr)
            return False
    except Exception as e:
        logger.error(f"Erro ao executar migrações: {e}")
        return False
    
    return True

def start_app():
    """Inicia a aplicação Flask."""
    logger.info("Iniciando aplicação...")
    
    app_script = os.path.join(os.path.dirname(__file__), "App", "app.py")
    
    try:
        # Muda para o diretório da app
        os.chdir(os.path.join(os.path.dirname(__file__), "App"))
        
        # Executa a aplicação
        subprocess.run([sys.executable, "app.py"])
    except KeyboardInterrupt:
        logger.info("\nAplicação finalizada pelo usuário.")
    except Exception as e:
        logger.error(f"Erro ao iniciar aplicação: {e}")

def main():
    """Função principal."""
    logger.info("Inicializando AnalyticSQL...")
    
    # Verifica se o arquivo .env existe
    env_file = os.path.join(os.path.dirname(__file__), "App", ".env")
    if not os.path.exists(env_file):
        print(f"⚠️  Arquivo .env não encontrado em {env_file}")
        print("Certifique-se de configurar as variáveis de ambiente necessárias:")
        print("   - GEMINI_API_KEY")
        print("   - DATABASE_URL (opcional)")
        return 1
    
    # Executa migrações
    if not run_migration():
        print("Falha nas migrações. Aplicação não será iniciada.")
        return 1
    
    # Inicia aplicação
    start_app()
    
    return 0

if __name__ == "__main__":
    exit(main())
