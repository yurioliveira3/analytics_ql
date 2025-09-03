"""
Factory para criação de modelos LLM baseado em configuração.
Centraliza a lógica de instanciação e configuração dos diferentes provedores.
"""

import os
from typing import Dict, Type, Optional
from enum import Enum

from .llm_interface import LLMAdapter, LLMConfig
from .adapters import GeminiAdapter, OllamaAdapter
from .logger import get_logger

logger = get_logger(__name__)


class LLMProvider(Enum):
    """
    Enum com os provedores LLM suportados.
    """
    GEMINI = "gemini"
    OLLAMA = "ollama"


class LLMFactory:
    """
    Factory para criação de instâncias LLM baseadas em configuração.
    """
    
    # Mapeamento de provedores para suas classes adaptadoras
    _ADAPTERS: Dict[LLMProvider, Type[LLMAdapter]] = {
        LLMProvider.GEMINI: GeminiAdapter,
        LLMProvider.OLLAMA: OllamaAdapter,
    }
    
    # Configurações padrão para cada tipo de modelo
    _DEFAULT_CONFIGS = {
        "sql": {
            LLMProvider.GEMINI: LLMConfig(
                model_name="gemini-2.0-flash-lite",
                temperature=0.0,
                top_p=0.5,
                top_k=60,
                max_tokens=1024,
                candidate_count=3,  # Gera 3 candidatos para reranking
                response_format="json",
                system_instruction=(
                    "Você é um especialista em SQL para PostgreSQL. "
                    "Retorne SEMPRE um JSON válido seguindo o schema acordado. "
                    "Nunca utilize aliases que formem termos ofensivos, constrangedores ou inadequados em português, inglês ou outros idiomas. "
                    "Prefira abreviações neutras e profissionais."
                )
            ),
            LLMProvider.OLLAMA: LLMConfig(
                model_name=os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b"),
                temperature=0.1,  # Baixa temperatura para SQL consistente
                top_p=0.6,        # Reduzido para modelo menor ser mais focado
                max_tokens=2048,  # Aumentado para queries SQL mais complexas
                candidate_count=1,  # Ollama não suporta múltiplos candidatos
                response_format="json",
                seed=42,  # Para reproduzibilidade
                stop=["</sql>", "<|im_end|>", "\n\n#"],  # Sequências de parada otimizadas
                system_instruction=(
                    "Você é um especialista em SQL para PostgreSQL. "
                    "Retorne SEMPRE um JSON válido seguindo exatamente o schema acordado. "
                    "Seja preciso e eficiente. Use sintaxe PostgreSQL moderna. "
                    "Nunca utilize aliases que formem termos ofensivos, constrangedores ou inadequados em português, inglês ou outros idiomas. "
                    "Prefira abreviações neutras e profissionais."
                )
            )
        },
        "insights": {
            LLMProvider.GEMINI: LLMConfig(
                model_name="gemini-1.5-flash",
                temperature=0.2,
                top_p=0.9,
                top_k=70,
                max_tokens=512,
                candidate_count=1,  # Insights só precisa de 1 candidato
                response_format="text",
                system_instruction=(
                    "Você é um especialista em análise de dados que gera insights de negócio "
                    "com base num payload JSON. Seja sucinto e valide a consistência do JSON. "
                    "Nunca utilize aliases que formem termos ofensivos, constrangedores ou inadequados em português, inglês ou outros idiomas. "
                    "Prefira abreviações neutras e profissionais."
                )
            ),
            LLMProvider.OLLAMA: LLMConfig(
                model_name=os.environ.get("OLLAMA_MODEL", "qwen2.5-coder:1.5b"),
                temperature=0.3,   # Mais criativo para insights
                top_p=0.8,         # Mais diversidade para insights
                max_tokens=1024,   # Suficiente para insights
                candidate_count=1,  # Ollama sempre 1 candidato
                response_format="text",
                seed=42,  # Para reproduzibilidade
                system_instruction=(
                    "Você é um especialista em análise de dados que gera insights de negócio "
                    "com base num payload JSON. Seja sucinto, claro e valide a consistência do JSON. "
                    "Foque em padrões, tendências e recomendações práticas. "
                    "Nunca utilize aliases que formem termos ofensivos, constrangedores ou inadequados em português, inglês ou outros idiomas. "
                    "Prefira abreviações neutras e profissionais."
                )
            )
        }
    }
    
    @classmethod
    def get_provider_from_env(cls) -> LLMProvider:
        """
        Obtém o provedor configurado nas variáveis de ambiente.
        
        Returns:
            LLMProvider: Provedor configurado ou GEMINI como padrão
        """
        provider_str = os.environ.get("LLM_PROVIDER", "gemini").lower()
        
        try:
            return LLMProvider(provider_str)
        except ValueError:
            logger.warning(f"Provedor '{provider_str}' não suportado. Usando Gemini como padrão.")
            return LLMProvider.GEMINI
    
    @classmethod
    def create_model(cls, model_type: str, provider: Optional[LLMProvider] = None, config: Optional[LLMConfig] = None) -> LLMAdapter:
        """
        Cria uma instância de modelo LLM baseada no tipo e provedor.
        
        Args:
            model_type: Tipo do modelo ("sql" ou "insights")
            provider: Provedor LLM (opcional, usa o configurado no env)
            config: Configuração customizada (opcional, usa padrão)
            
        Returns:
            LLMAdapter: Instância do modelo configurado
            
        Raises:
            ValueError: Se o tipo de modelo não for suportado
            RuntimeError: Se o provedor não estiver disponível
        """
        # Usa provedor do ambiente se não especificado
        if provider is None:
            provider = cls.get_provider_from_env()
        
        # Valida tipo de modelo
        if model_type not in cls._DEFAULT_CONFIGS:
            raise ValueError(f"Tipo de modelo '{model_type}' não suportado. Tipos disponíveis: {list(cls._DEFAULT_CONFIGS.keys())}")
        
        # Usa configuração padrão se não especificada
        if config is None:
            config = cls._DEFAULT_CONFIGS[model_type][provider]
        
        # Obtém classe do adaptador
        adapter_class = cls._ADAPTERS.get(provider)
        if not adapter_class:
            raise ValueError(f"Provedor '{provider.value}' não tem adaptador implementado")
        
        # Cria instância do adaptador
        try:
            adapter = adapter_class(config)
            
            # Verifica se está disponível
            if not adapter.is_available():
                raise RuntimeError(f"Provedor '{provider.value}' não está disponível ou não está configurado corretamente")
            
            logger.info(f"Modelo '{model_type}' criado com sucesso usando {provider.value} ({config.model_name})")
            return adapter
            
        except Exception as e:
            logger.error(f"Erro ao criar modelo '{model_type}' com provedor '{provider.value}': {e}")
            raise
    
    @classmethod
    def create_sql_model(cls, provider: Optional[LLMProvider] = None) -> LLMAdapter:
        """
        Cria modelo para geração de SQL.
        """
        return cls.create_model("sql", provider)
    
    @classmethod
    def create_insights_model(cls, provider: Optional[LLMProvider] = None) -> LLMAdapter:
        """
        Cria modelo para geração de insights.
        """
        return cls.create_model("insights", provider)
    
    @classmethod
    def list_available_providers(cls) -> Dict[str, bool]:
        """
        Lista todos os provedores e sua disponibilidade.
        
        Returns:
            Dict[str, bool]: Dicionário com provedor e status de disponibilidade
        """
        availability = {}
        
        for provider in LLMProvider:
            try:
                # Tenta criar um modelo de teste para verificar disponibilidade
                adapter_class = cls._ADAPTERS[provider]
                test_config = cls._DEFAULT_CONFIGS["sql"][provider]
                adapter = adapter_class(test_config)
                availability[provider.value] = adapter.is_available()
            except Exception:
                availability[provider.value] = False
        
        return availability
