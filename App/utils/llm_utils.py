"""
Utilitários para interação com modelos de linguagem (LLMs).
"""

import os
import time
import pandas as pd
from google.api_core.exceptions import ResourceExhausted
from utils.logger import get_logger
from utils.llm_interface import LLMAdapter, LLMResponse

# Logger para este módulo
logger = get_logger(__name__)


def safe_send_message(model, prompt, history=None, retries=5, backoff_factor=2):
    """
    Envia uma mensagem ao modelo LLM de forma segura.
    Agora suporta tanto modelos Gemini (legacy) quanto novos adaptadores LLM.
    
    Args:
        model: Modelo LLM (pode ser Gemini antigo ou novo LLMAdapter)
        prompt: Prompt a ser enviado
        history: Histórico de conversas (opcional)
        retries: Número de tentativas
        backoff_factor: Fator de backoff exponencial
        
    Returns:
        Resposta do modelo (compatível com código existente)
    """
    # Detecta se é o novo adaptador ou modelo Gemini legado
    is_new_adapter = isinstance(model, LLMAdapter)
    
    attempt = 0
    while attempt < retries:
        try:
            if is_new_adapter:
               
                # Usa nova interface LLMAdapter
                response = model.generate_content(prompt)
                
                # Cria objeto compatível com código existente
                class CompatibleResponse:
                    def __init__(self, llm_response: LLMResponse):
                        self.text = llm_response.text
                        self._llm_response = llm_response
                        
                        # Tenta expor candidates se a resposta original tiver
                        if (hasattr(llm_response, 'raw_response') and 
                            hasattr(llm_response.raw_response, 'candidates')):
                            self.candidates = llm_response.raw_response.candidates
                        else:
                            self.candidates = None
                
                compatible_response = CompatibleResponse(response)
                
                if history is not None:
                    history.append({"prompt": prompt, "response": response.text})
                
                return compatible_response
            else:
                # Usa interface Gemini legada (para compatibilidade)
                response = model.generate_content(prompt)
                if history is not None:
                    history.append({"prompt": prompt, "response": response.text})
                return response
                
        except ResourceExhausted as e:
            attempt += 1
            if attempt < retries:
                wait_time = backoff_factor ** attempt
                logger.warning(f"Limite de requisições atingido. Tentando novamente em {wait_time} segundos... (Tentativa {attempt}/{retries})")
                time.sleep(wait_time)
            else:
                logger.error("Máximo de tentativas atingido para ResourceExhausted.")
                break
        except Exception as e:
            # Para adaptadores, tenta detectar se é erro de rate limit
            if is_new_adapter and ("rate" in str(e).lower() or "limit" in str(e).lower()):
                attempt += 1
                if attempt < retries:
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Possível limite de requisições atingido. Tentando novamente em {wait_time} segundos... (Tentativa {attempt}/{retries})")
                    time.sleep(wait_time)
                    continue
            
            logger.error(f"Erro inesperado ao enviar mensagem para o modelo: {e}", exc_info=True)
            break
    
    raise Exception("Máximo de tentativas atingido.")


def read_prompt_file(file_path: str) -> str:
    """
    Lê o conteúdo de um arquivo de prompt.
    
    Args:
        file_path: Caminho para o arquivo de prompt
        
    Returns:
        Conteúdo do arquivo ou prompt padrão
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback para o caso de o arquivo não ser encontrado no ambiente de execução
        return "Você é um especialista em SQL. Crie uma query para: {natural_language_query} com base em: {context}"


def generate_insights_payload(last_entry: dict, result: pd.DataFrame | str, dataframe_analysis_df: pd.DataFrame | None = None, ml_algorithm: str | None = None, chart_type: str | None = None, regression_info: dict | None = None) -> dict:
    """
    Monta o payload JSON para geração de insights.

    Args:
        last_entry: Última entrada do histórico da sessão.
        result: Resultado da execução da query (DataFrame ou erro).
        dataframe_analysis_df: DataFrame com análise descritiva (opcional).
        ml_algorithm: Algoritmo de ML utilizado (opcional).
        chart_type: Tipo de gráfico gerado (opcional).
        regression_info: Informações da análise de regressão linear (opcional).

    Returns:
        Dicionário pronto para envio ao modelo de insights.
    """
    try:
        summary_stats = dataframe_analysis_df.to_dict(orient="index") if dataframe_analysis_df is not None else {}
    except Exception:
        summary_stats = {}
    try:
        sample = result.head(500) if isinstance(result, pd.DataFrame) else pd.DataFrame()
        data_sample = sample.to_dict(orient="records")
    except Exception:
        data_sample = []

    # Se summary_stats estiver vazio, indica que não havia dados numéricos para análise descritiva
    payload = {
        "natural_language_query": last_entry.get("nl_query", ""),
        "sql_query": last_entry.get("executed_query", ""),
        # Não agrega valor aos insights, mas pode ser útil para depuração
        #"sql_resume": last_entry.get("explanation", ""),
        #"execution_metrics": { 
        #    "execution_time_ms": last_entry.get("execution_time_ms", 0),
        #    "plan_total_cost": last_entry.get("total_cost", 0),
        #    "plan_rows": last_entry.get("plan_rows", 0),
        #},
        "summary_stats": summary_stats if summary_stats else "Sem dados numéricos para análise descritiva.",
        "schema_metadata": last_entry.get("used_tables", []),
        "data_sample": data_sample if data_sample else [],
        "ml_algorithm": ml_algorithm if ml_algorithm else "Nenhum algoritmo de ML aplicado",
        #"ml_result": ml_result if ml_result is not None else None,
        "chart_type": chart_type if chart_type else "Nenhum gráfico sugerido",
        "regression_analysis": regression_info if regression_info else "Nenhuma análise de regressão aplicada"
    }
    
    return payload
