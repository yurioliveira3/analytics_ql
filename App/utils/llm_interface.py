"""
Interface comum para todos os provedores de LLM.
Define o contrato que todos os adaptadores devem implementar.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """
    Resposta padronizada de qualquer provedor LLM.
    """
    text: str
    raw_response: Any = None
    metadata: Optional[Dict] = None


@dataclass
class LLMConfig:
    """
    Configuração base para modelos LLM.
    """
    model_name: str
    temperature: float = 0.0
    max_tokens: int = 1024
    top_p: float = 0.9
    top_k: Optional[int] = None
    system_instruction: Optional[str] = None
    response_format: str = "text"  # "text" ou "json"
    candidate_count: int = 3  # Número de candidatos (específico Gemini)
    
    # Parâmetros adicionais suportados por Ollama
    seed: Optional[int] = None  # Para reproduzibilidade
    stop: Optional[List[str]] = None  # Sequências de parada
    frequency_penalty: Optional[float] = None  # Penalidade por frequência (0.0 a 2.0)
    presence_penalty: Optional[float] = None  # Penalidade por presença (0.0 a 2.0)


class LLMAdapter(ABC):
    """
    Interface abstrata que todos os adaptadores de LLM devem implementar.
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
    
    @abstractmethod
    def generate_content(self, prompt: str) -> LLMResponse:
        """
        Gera conteúdo baseado no prompt fornecido.
        
        Args:
            prompt: O prompt a ser enviado ao modelo
            
        Returns:
            LLMResponse: Resposta padronizada do modelo
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica se o provedor está disponível e configurado corretamente.
        
        Returns:
            bool: True se disponível, False caso contrário
        """
        pass
    
    @abstractmethod
    def get_provider_name(self) -> str:
        """
        Retorna o nome do provedor.
        
        Returns:
            str: Nome do provedor (ex: "gemini", "ollama")
        """
        pass
