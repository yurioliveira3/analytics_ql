"""
Sistema de logging centralizado para o Analytics QL.
"""

from datetime import datetime
from pathlib import Path
import logging

def setup_logger(name: str = __name__, level: str = "INFO") -> logging.Logger:
    """
    Configura e retorna um logger configurado para o projeto.
    
    Args:
        name: Nome do logger (geralmente __name__ do módulo)
        level: Nível de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Logger configurado
    """
    # Cria o diretório de logs se não existir
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # Nome do arquivo de log baseado na data
    log_filename = f"analytics_ql_{datetime.now().strftime('%Y%m%d')}.log"
    log_path = log_dir / log_filename
    
    # Cria o logger
    logger = logging.getLogger(name)
    
    # Evita duplicação de handlers se o logger já foi configurado
    if logger.handlers:
        return logger
    
    # Define o nível
    numeric_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(numeric_level)
    
    # Formato das mensagens
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler para arquivo
    file_handler = logging.FileHandler(log_path, encoding='utf-8')
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)
    
    # Handler para console (apenas INFO e acima)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Adiciona os handlers
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Logger principal do projeto
main_logger = setup_logger("analytics_ql")

# Função de conveniência para outros módulos
def get_logger(name: str = None) -> logging.Logger:
    """
    Retorna um logger configurado para o módulo específico.
    
    Args:
        name: Nome do módulo (se None, usa o logger principal)
    
    Returns:
        Logger configurado
    """
    if name:
        return setup_logger(name)
    return main_logger
