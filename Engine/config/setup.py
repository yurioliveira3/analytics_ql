# c:\projects\Analytics_IA\config\setup.py
from google.api_core.exceptions import ResourceExhausted
import google.generativeai as genai
from dotenv import load_dotenv
from datetime import datetime
import logging
import os

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Configurações do Google Gemini ---
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("A variável de ambiente GOOGLE_API_KEY não foi definida.")
genai.configure(api_key=GOOGLE_API_KEY)

# --- Configurações do Banco de Dados PostgreSQL ---
DB_USER = os.getenv("DB_USER", "postgresql")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "analytics_db")

# String de conexão para psycopg
DB_DSN = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# --- Configurações Gerais ---
DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_ambiente_dinamico() -> str:
    """Retorna o ambiente com base no host do banco."""
    if "localhost" in DB_HOST or "127.0.0.1" in DB_HOST:
        return "DEV"
    # Adicione outras lógicas se necessário (ex: 'homolog', 'prod')
    return "PROD"

def setup_logging(schema_name: str, app_name: str) -> logging.Logger:
    """Configura o logger para a aplicação.

    Args:
        schema_name: Nome do schema do banco.
        app_name: Nome da aplicação.

    Returns:
        Logger configurado para arquivo e console.
    """
    logs_dir = os.path.join(DIR, "logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    log_file = os.path.join(
        logs_dir,
        f"{schema_name}_{app_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.INFO)
    
    # Evita adicionar handlers duplicados
    if not logger.handlers:
        # Handler para o arquivo (data/hora/minuto/segundo)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

        # Handler para o console (printa até minuto)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter("%(asctime)s - %(message)s", datefmt="%Y-%m-%d %H:%M")
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
        
    return logger

# Importação da exceção para ser acessível em outros módulos
__all__ = [
    "genai", "ResourceExhausted", "DB_DSN", "DIR", 
    "setup_logging", "get_ambiente_dinamico"
]