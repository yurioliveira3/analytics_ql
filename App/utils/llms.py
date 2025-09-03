"""
Configurações centralizadas dos modelos LLM (Large Language Models) - Nova Versão.
Utiliza o padrão Factory para suportar múltiplos provedores (Gemini, Ollama, etc.).

Para manter compatibilidade com código existente, ainda exporta as mesmas variáveis,
mas agora criadas através da Factory.
"""

from dotenv import load_dotenv
from utils.llm_factory import LLMFactory
from utils.logger import get_logger
import os

# Carrega variáveis de ambiente
load_dotenv()

# Logger para este módulo
logger = get_logger(__name__)

# Detecta se está em reload do Flask para reduzir logs duplicados
is_flask_reloading = os.environ.get('WERKZEUG_RUN_MAIN') == 'true'

# --- Modelos LLM usando Factory Pattern ---

try:
    # Modelo para geração de consultas SQL
    generative_model_sql = LLMFactory.create_sql_model()
    if not is_flask_reloading:  # Só loga na primeira inicialização
        logger.info(f"Modelo SQL inicializado: {generative_model_sql.get_provider_name()}")
    
except Exception as e:
    logger.error(f"Erro ao inicializar modelo SQL: {e}")
    # Fallback para None - código que usar deve verificar se está None
    generative_model_sql = None

try:
    # Modelo para geração de insights  
    generative_model_insights = LLMFactory.create_insights_model()
    if not is_flask_reloading:  # Só loga na primeira inicialização
        logger.info(f"Modelo Insights inicializado: {generative_model_insights.get_provider_name()}")
    
except Exception as e:
    logger.error(f"Erro ao inicializar modelo Insights: {e}")
    # Fallback para None - código que usar deve verificar se está None
    generative_model_insights = None

# Função auxiliar para verificar status dos modelos
def get_models_status():
    """
    Retorna o status dos modelos inicializados.
    
    Returns:
        dict: Status de cada modelo
    """
    return {
        "sql_model": {
            "initialized": generative_model_sql is not None,
            "provider": generative_model_sql.get_provider_name() if generative_model_sql else None,
            "available": generative_model_sql.is_available() if generative_model_sql else False
        },
        "insights_model": {
            "initialized": generative_model_insights is not None,
            "provider": generative_model_insights.get_provider_name() if generative_model_insights else None,
            "available": generative_model_insights.is_available() if generative_model_insights else False
        },
        "available_providers": LLMFactory.list_available_providers()
    }

# Função para recriar modelos (útil para testes ou mudança de configuração)
def recreate_models():
    """
    Recria os modelos LLM. Útil quando as configurações mudam.
    """
    global generative_model_sql, generative_model_insights
    
    try:
        generative_model_sql = LLMFactory.create_sql_model()
        logger.info(f"Modelo SQL recriado: {generative_model_sql.get_provider_name()}")
    except Exception as e:
        logger.error(f"Erro ao recriar modelo SQL: {e}")
        generative_model_sql = None
    
    try:
        generative_model_insights = LLMFactory.create_insights_model()
        logger.info(f"Modelo Insights recriado: {generative_model_insights.get_provider_name()}")
    except Exception as e:
        logger.error(f"Erro ao recriar modelo Insights: {e}")
        generative_model_insights = None
