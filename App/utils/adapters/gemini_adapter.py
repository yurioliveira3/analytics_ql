"""
Adaptador para o Google Gemini.
Mantém a compatibilidade com a implementação existente.
"""

import os
import google.generativeai as genai
from typing import Optional
from google.api_core.exceptions import ResourceExhausted

from ..llm_interface import LLMAdapter, LLMConfig, LLMResponse
from ..logger import get_logger

logger = get_logger(__name__)


class GeminiAdapter(LLMAdapter):
    """
    Adaptador para modelos Google Gemini.
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self._model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """
        Inicializa o modelo Gemini com as configurações fornecidas.
        """
        try:
            # Configura a API Key
            api_key = os.environ.get("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY não encontrada nas variáveis de ambiente")
            
            genai.configure(api_key=api_key)
            
            # Configura parâmetros de geração baseados no config
            generation_config = genai.types.GenerationConfig(
                temperature=self.config.temperature,
                top_p=self.config.top_p,
                max_output_tokens=self.config.max_tokens,
                candidate_count=self.config.candidate_count,  # Usa configuração dinâmica
                response_mime_type="application/json" if self.config.response_format == "json" else "text/plain"
            )
            
            # Adiciona parâmetros opcionais se definidos
            if self.config.top_k is not None:
                generation_config.top_k = self.config.top_k
            
            if self.config.seed is not None:
                generation_config.seed = self.config.seed
            
            if self.config.stop is not None:
                generation_config.stop_sequences = self.config.stop
            
            if self.config.frequency_penalty is not None:
                generation_config.frequency_penalty = self.config.frequency_penalty
            
            if self.config.presence_penalty is not None:
                generation_config.presence_penalty = self.config.presence_penalty
            
            # Cria o modelo
            self._model = genai.GenerativeModel(
                model_name=self.config.model_name,
                generation_config=generation_config,
                system_instruction=self.config.system_instruction
            )
            
            logger.info(f"Modelo Gemini '{self.config.model_name}' inicializado com sucesso")
            
        except Exception as e:
            logger.error(f"Erro ao inicializar modelo Gemini: {e}")
            self._model = None
    
    def generate_content(self, prompt: str) -> LLMResponse:
        """
        Gera conteúdo usando o modelo Gemini.
        """
        if not self._model:
            raise RuntimeError("Modelo Gemini não inicializado")
        
        try:
            response = self._model.generate_content(prompt)
            
            # Extrai texto de forma robusta
            try:
                # Primeira tentativa: response.text (funciona se há só 1 candidato)
                response_text = response.text
            except ValueError:
                # Segunda tentativa: acessa o primeiro candidato diretamente
                try:
                    response_text = response.candidates[0].content.parts[0].text
                    logger.debug(f"Gemini retornou {len(response.candidates)} candidatos, usando o primeiro")
                except (IndexError, AttributeError) as e:
                    logger.error(f"Erro ao extrair texto da resposta Gemini: {e}")
                    raise RuntimeError(f"Não foi possível extrair texto da resposta: {e}")
            
            return LLMResponse(
                text=response_text,
                raw_response=response,
                metadata={
                    "provider": "gemini",
                    "model": self.config.model_name,
                    "candidate_count": len(response.candidates),
                    "finish_reason": getattr(response.candidates[0], "finish_reason", None) if response.candidates else None
                }
            )
            
        except ResourceExhausted as e:
            logger.error(f"Limite de requisições atingido no Gemini: {e}")
            raise
        except Exception as e:
            logger.error(f"Erro ao gerar conteúdo com Gemini: {e}")
            raise
    
    def is_available(self) -> bool:
        """
        Verifica se o Gemini está disponível.
        """
        return (
            self._model is not None and 
            os.environ.get("GOOGLE_API_KEY") is not None
        )
    
    def get_provider_name(self) -> str:
        """
        Retorna o nome do provedor.
        """
        return "gemini"
