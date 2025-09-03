"""
Módulo principal para conversão de linguagem natural para SQL.
"""

import os
import json
from utils.config import vector_store, DIR_PATH, embedding_function
from utils.llms import generative_model_sql
from utils.logger import get_logger
from utils.first_layer import (
    is_greeting_or_small_talk,
    is_vague_question,
    log_interaction_type,
    create_greeting_response,
    create_vague_question_response
)
from utils.llm_utils import safe_send_message, read_prompt_file
from utils.sql_operations import normalize_sql, pick_best_query, is_query_safe

# Logger para este módulo
logger = get_logger(__name__)


def get_sql_from_text(natural_language_query: str, db_name: str) -> tuple[str, str, list[str], str]:
    """
    Gera uma consulta SQL a partir de uma pergunta em linguagem natural.

    1. Verifica se é uma saudação/cumprimento e responde diretamente se for.
    2. Busca metadados relevantes no banco vetorial (PGVector).
    3. Monta um contexto com os metadados encontrados.
    4. Gera uma consulta SQL a partir de uma pergunta em linguagem natural em duas etapas:
        4.1. Gera 3 consultas SQL candidatas usando o Gemini.
        4.2. Usa o Gemini novamente para selecionar a melhor consulta entre as candidatas.

    Args:
        natural_language_query: Pergunta em linguagem natural
        db_name: Nome do banco de dados
        
    Returns:
        Tuple contendo a query SQL, explicação, lista de tabelas usadas e algoritmo ML.
    """
    
    # Primeira verificação: detecta saudações antes de processar
    if is_greeting_or_small_talk(natural_language_query):
        log_interaction_type(natural_language_query, "greeting")
        logger.info(f"Saudação detectada: '{natural_language_query}' - Respondendo diretamente sem consultar modelo")
        return create_greeting_response()
    
    # Segunda verificação: detecta perguntas muito vagas
    if is_vague_question(natural_language_query):
        log_interaction_type(natural_language_query, "vague_question")
        logger.info(f"Pergunta vaga detectada: '{natural_language_query}' - Solicitando mais especificidade")
        return create_vague_question_response()

    # Se não cair nas primeiras verificações, busca por similaridade no PGVector
    try:

        vec = embedding_function.embed_query(natural_language_query)

        # Busca apenas metadados de objetos que suportam SELECT
        results = vector_store.similarity_search_by_vector(
            vec,
            k=30,
            filter={
                "tipo": ["TABLE", "VIEW", "MATERIALIZED_VIEW"] # "FUNCTION" e "SEQUENCE" - Adicionar se necessário
            }
        )

    except Exception as e:
        return f"-- Erro ao conectar ao Vector Store: {e}", "", []

    if not results:
        log_interaction_type(natural_language_query, "no_metadata_found")
        return "-- Nenhum metadado relevante encontrado para a pergunta.", "", [], ""

    # Log da consulta válida sendo processada
    log_interaction_type(natural_language_query, "valid_query_processing")

    # Monta contexto usando page_content e campo cmetadata de cada documento
    context = "\n".join([
        f"{doc.page_content}\nMetadata:\n{ {k: v for k, v in doc.metadata.items() if k not in ['linhas', 'resumo']} }\n\n"
        for doc in results
    ])
   
    prompt_template_generation = read_prompt_file(
        os.path.join(DIR_PATH, "prompts", "sql_generation.txt")
    )

    # Escapa chaves literais para evitar KeyError
    prompt_template_generation = prompt_template_generation.replace("{", "{{").replace("}", "}}")
    prompt_template_generation = prompt_template_generation.replace("{{natural_language_query}}", "{natural_language_query}").replace("{{context}}", "{context}").replace("{{db_name}}", "{db_name}")

    prompt_generation = prompt_template_generation.format(
        natural_language_query=natural_language_query,
        context=context,
        db_name=db_name
    )

    #Chamada do Gemini para gerar as 3 queries candidatas
    try:
        response = safe_send_message(generative_model_sql, prompt_generation)
        
        # Verificar se é resposta da nova arquitetura ou Gemini legado
        if hasattr(response, '_llm_response'):
            # Nova arquitetura - acessar dados da resposta original
            raw_response = response._llm_response.raw_response
            if hasattr(raw_response, 'candidates') and raw_response.candidates:
                candidates = raw_response.candidates
            else:
                # Fallback: tentar parsear o texto diretamente
                candidates = None
                response_text = response.text
        elif hasattr(response, 'candidates'):
            # Gemini legado - usar diretamente
            candidates = response.candidates
            response_text = response.text
        else:
            # Fallback para qualquer outro caso
            candidates = None
            response_text = response.text if hasattr(response, 'text') else str(response)
        
        # Se não temos candidates, tenta parsear o texto diretamente
        if not candidates:
            try:
                # Tenta parsear como JSON único
                json_response = json.loads(response_text)
                if isinstance(json_response, list):
                    # Lista de candidatos
                    sql_candidates = []
                    ml_algorithms = []
                    explanations = []
                    for item in json_response:
                        raw_sql = item.get("sql_query", "")
                        normalized_sql = normalize_sql(raw_sql) if raw_sql else ""
                        if normalized_sql:
                            sql_candidates.append(normalized_sql)
                            ml_algorithms.append(item.get("ml_algorithm", ""))
                            explanations.append(item.get("explanation", ""))
                            used_tables = item.get("used_tables", [])
                            if isinstance(used_tables, list):
                                used_tables_list = used_tables
                else:
                    # Objeto único
                    raw_sql = json_response.get("sql_query", "")
                    normalized_sql = normalize_sql(raw_sql) if raw_sql else ""
                    sql_candidates = [normalized_sql] if normalized_sql else []
                    ml_algorithms = [json_response.get("ml_algorithm", "")]
                    explanations = [json_response.get("explanation", "")]
                    used_tables = json_response.get("used_tables", [])
                    if isinstance(used_tables, list):
                        used_tables_list = used_tables
            except json.JSONDecodeError:
                logger.error(f"Não foi possível parsear resposta como JSON: {response_text[:200]}...")
                return "-- Erro ao processar resposta do modelo.", "", [], ""
        else:
            # Processar candidates tradicional do Gemini
            sql_candidates = []
            ml_algorithms = []
            used_tables_list = []
            explanations = []  # Lista de explicações por candidato
            for candidate in candidates:
                try:
                    json_text = candidate.content.parts[0].text
                    json_response = json.loads(json_text)
                    raw_sql = json_response.get("sql_query", "")
                    normalized_sql = normalize_sql(raw_sql) if raw_sql else ""
                    sql_candidates.append(normalized_sql)
                    # capture ml algorithm for each candidate
                    ml_algorithms.append(json_response.get("ml_algorithm", ""))
                    # capture explanation for each candidate
                    explanations.append(json_response.get("explanation", ""))
                     # Captura used_tables se existir
                    used_tables = json_response.get("used_tables", [])
                    if isinstance(used_tables, list):
                        used_tables_list = used_tables
                except (json.JSONDecodeError, IndexError, AttributeError):
                    continue

        if not sql_candidates:
            return "-- Nenhuma query válida foi gerada.", "", [], ""

        # Se vierem menos de 3, filtramos candidatos vazios
        sql_candidates = [q for q in sql_candidates if q]

    except (Exception, json.JSONDecodeError) as e:
        logger.error(f"Erro ao gerar ou decodificar candidatas: {e}")
        return f"-- Erro ao gerar as queries candidatas: {e}", "", [], ""

    # Reranking das queries candidatas com modelo CrossEncoder
    try:
        ranked = pick_best_query(natural_language_query, sql_candidates, top_k=1)
        selected_sql = ranked[0]["sql"]
        # Obtém explicação correspondente ao SQL selecionado
        try:
            idx = sql_candidates.index(selected_sql)
            explanation = explanations[idx]
        except (ValueError, IndexError):
            explanation = f"Consulta selecionada pelo reranker (score={ranked[0]['final_score']:.4f})."
        if not selected_sql or not is_query_safe(selected_sql):
            return "-- A query gerada foi bloqueada por razões de segurança.", explanation, used_tables_list, ""
        # determine ml algorithm corresponding to the selected SQL
        try:
            idx_ml = sql_candidates.index(selected_sql)
            chosen_ml = ml_algorithms[idx_ml]
        except ValueError:
            chosen_ml = ""
        return selected_sql, explanation, used_tables_list, chosen_ml

    except Exception as e:
        return f"-- Erro ao reranquear as consultas candidatas: {e}", "", used_tables_list, ""
