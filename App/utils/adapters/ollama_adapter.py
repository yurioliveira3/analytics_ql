"""
Adaptador para Ollama (modelos locais).
Permite usar modelos como gpt-oss:20b via API compatível com OpenAI.
"""

import os
import requests
from openai import OpenAI
from typing import Optional

from ..llm_interface import LLMAdapter, LLMConfig, LLMResponse
from ..logger import get_logger

logger = get_logger(__name__)


class OllamaAdapter(LLMAdapter):
    """
    Adaptador para modelos Ollama usando API compatível com OpenAI.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._client = None
        self._base_url = None
        self._initialize_client()
    
    def _initialize_client(self):
        """
        Inicializa o cliente OpenAI configurado para Ollama.
        """
        try:
            # Configura URL base do Ollama
            self._base_url = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434/v1")
            
            # Ollama não precisa de API key real, mas o cliente OpenAI exige
            api_key = os.environ.get("OLLAMA_API_KEY", "ollama")
            
            self._client = OpenAI(
                api_key=api_key,
                base_url=self._base_url
            )
            
            logger.info(f"Cliente Ollama inicializado com sucesso (URL: {self._base_url})")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar cliente Ollama: {e}")
            self._client = None
    
    def _check_ollama_health(self) -> bool:
        """
        Verifica se o Ollama está rodando e acessível.
        """
        try:
            # Remove "/v1" da URL para verificar saúde do Ollama
            health_url = self._base_url.replace("/v1", "") + "/api/tags"
            response = requests.get(health_url, timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def generate_content(self, prompt: str) -> LLMResponse:
        """
        Gera conteúdo usando o modelo Ollama.
        """
        if not self._client:
            raise RuntimeError("Cliente Ollama não inicializado")
        
        if not self._check_ollama_health():
            raise RuntimeError(f"Ollama não está acessível em {self._base_url}")
        
        try:
            # Prepara mensagens baseadas no system instruction
            messages = []
            
            if self.config.system_instruction:
                messages.append({
                    "role": "system", 
                    "content": self.config.system_instruction
                })
            
            messages.append({
                "role": "user", 
                "content": prompt
            })
            
            # Prepara parâmetros para o Ollama
            # Nota: candidate_count é ignorado - Ollama não suporta múltiplos candidatos
            kwargs = {
                "model": self.config.model_name,
                "messages": messages,
                "temperature": self.config.temperature,
                "max_tokens": self.config.max_tokens,
                "top_p": self.config.top_p,
            }
            
            # Adiciona parâmetros opcionais se definidos
            # Nota: top_k não é suportado pela API OpenAI (compatibilidade)
            # if self.config.top_k is not None:
            #     kwargs["top_k"] = self.config.top_k
            
            if self.config.seed is not None:
                kwargs["seed"] = self.config.seed
            
            if self.config.stop is not None:
                kwargs["stop"] = self.config.stop
            
            if self.config.frequency_penalty is not None:
                kwargs["frequency_penalty"] = self.config.frequency_penalty
            
            if self.config.presence_penalty is not None:
                kwargs["presence_penalty"] = self.config.presence_penalty
            
            # Para JSON, garante que o formato seja explícito
            if self.config.response_format == "json":
                # Qwen2.5-Coder entende bem instruções diretas para JSON
                json_prompt = (
                    "Você DEVE responder APENAS com um JSON válido que siga exatamente o schema especificado. "
                    "Não inclua explicações, comentários ou texto adicional fora do JSON. "
                    "O JSON deve começar com { e terminar com }."
                )
                if messages[-1]["content"]:
                    messages[-1]["content"] += f"\n\n{json_prompt}"
            
            response = self._client.chat.completions.create(**kwargs)
            
            return LLMResponse(
                text=response.choices[0].message.content,
                raw_response=response,
                metadata={
                    "provider": "ollama",
                    "model": self.config.model_name,
                    "finish_reason": response.choices[0].finish_reason,
                    "base_url": self._base_url
                }
            )
            
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo com Ollama: {e}")
            raise
    
    def is_available(self) -> bool:
        """
        Verifica se o Ollama está disponível.
        """
        return (
            self._client is not None and 
            self._check_ollama_health()
        )
    
    def get_provider_name(self) -> str:
        """
        Retorna o nome do provedor.
        """
        return "ollama"
