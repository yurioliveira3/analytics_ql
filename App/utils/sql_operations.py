"""
Operações SQL: validação, execução, análise de planos e ranking de queries.
"""

import os
import re
import time
import pandas as pd
import numpy as np
import sqlparse
from sqlalchemy import create_engine, text
from utils.logger import get_logger
from utils.constants import reranker_model

# Logger para este módulo
logger = get_logger(__name__)


def is_query_safe(sql_query: str) -> bool:
    """
    Verifica se a query SQL é segura (read-only) para execução.

    Args:
        sql_query: A consulta SQL a ser validada.

    Returns:
        True se a consulta for segura, False caso contrário.
    """
    # Regex para encontrar palavras-chave DML/DDL perigosas como palavras inteiras, case-insensitive.
    FORBIDDEN_KEYWORDS_PATTERN = re.compile(
        r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|MERGE)\b",
        re.IGNORECASE
    )
    if FORBIDDEN_KEYWORDS_PATTERN.search(sql_query):
        return False
    return True


def get_explain_plan(sql_query: str, engine) -> tuple[dict | None, str | None]:
    """
    Executa EXPLAIN (FORMAT JSON) na query, valida a sintaxe e retorna o plano.

    Args:
        sql_query: Consulta SQL a ser analisada.
        engine: Instância SQLAlchemy Engine.

    Returns:
        Uma tupla (plano, None) em caso de sucesso, ou (None, erro) se a
        sintaxe for inválida ou ocorrer outro erro.
    """
    try:
        with engine.connect() as connection:
            # Usar uma transação que será revertida para não deixar rastros
            with connection.begin() as transaction:
                explain_sql = f"EXPLAIN (FORMAT JSON) {sql_query}"
                result = connection.execute(text(explain_sql))
                plan_json = result.fetchone()[0]
                transaction.rollback()  # Garante que nada seja commitado
                # O resultado é uma lista JSON, pega o primeiro elemento
                plan = plan_json[0] if isinstance(plan_json, list) else plan_json
                return plan, None
    except Exception as exc:
        # Captura erros de sintaxe, tabelas/colunas inexistentes, etc.
        return None, str(exc)


def check_plan_limits(total_cost: float, plan_rows: int) -> tuple[bool, str]:
    """
    Verifica se o plano excede limites de custo ou linhas.

    Args:
        total_cost: Custo total do plano.
        plan_rows: Número de linhas do plano.

    Returns:
        (flag, motivo) - True se excedeu, motivo como string.
    """
    try:
        # Limites arbitrários, ajustar conforme realidade do banco
        if total_cost > 1000000 or plan_rows > 200000: 
            motivo = f"Plano excede limites: custo={total_cost}, linhas={plan_rows}"
            return True, motivo
        return False, ""
    except Exception as exc:
        return True, f"Erro ao analisar plano: {exc}"


def execute_sql_query(sql_query: str) -> pd.DataFrame | str:
    """
    Executa uma consulta SQL no banco de dados e retorna o resultado como um DataFrame.
    Antes, executa EXPLAIN para checar limites de custo/linhas.
    Salva o histórico da execução.
    
    Args:
        sql_query: Query SQL a ser executada
        
    Returns:
        Tupla com (DataFrame/erro, tempo_execução, custo_total, linhas_plano)
    """
    if not is_query_safe(sql_query):
        return "A query foi bloqueada por razões de segurança.", None, None, None

    try:
        engine = create_engine(os.environ.get("PG_CONNECTION_STRING"))

        # Valida sintaxe e obtém plano de execução em uma única etapa
        plan, erro = get_explain_plan(sql_query, engine)
        if erro:
            return f"Erro de sintaxe ou análise da query: {erro}", None, None, None
        if plan is None:
            return "Não foi possível obter o plano de execução (EXPLAIN).", None, None, None

        total_cost = plan.get("Plan", {}).get("Total Cost", 0)
        plan_rows = plan.get("Plan", {}).get("Plan Rows", 0)
        flag, motivo = check_plan_limits(total_cost, plan_rows)
        if flag:
            return f"Execução bloqueada: {motivo}", None, None, None

        start = time.time()
        with engine.connect() as connection:
            df = pd.read_sql_query(text(sql_query), connection)
            df = df.round(2) # Aplica round de 2 casas decimais nas colunas numéricas
        end = time.time()
        execution_time_ms = int((end - start) * 1000)
        log_query_history(sql_query, execution_time_ms, engine, total_cost, plan_rows)
        return df, execution_time_ms, total_cost, plan_rows
    except Exception as e:
        return f"Erro ao executar a query: {e}", None, None, None


def normalize_sql(q: str) -> str:
    """
    Normaliza o SQL retornado pelo modelo, removendo comentários e padronizando keywords.

    Args:
        q: Comando SQL a ser normalizado.

    Returns:
        SQL normalizado em uma única linha, keywords em maiúsculas.
    """
    q = sqlparse.format(q, strip_comments=True, keyword_case="upper", reindent=False)
    return " ".join(q.split())


def rule_score(sql: str, forbidden: tuple[str, ...] = ("DELETE","UPDATE","INSERT","ALTER"), penalize_star: bool = True) -> float:
    """
    Calcula heurística simples para consultas SQL.
    
    Args:
        sql: Query SQL a ser avaliada
        forbidden: Palavras-chave proibidas
        penalize_star: Se deve penalizar SELECT *
        
    Returns:
        Score da query (0.0 a 1.0)
    """
    s = 1.0
    up = sql.upper()
    if any(f in up for f in forbidden):
        return 0.0
    if penalize_star and "SELECT *" in up:
        s -= 0.1
    return max(0.0, s)


def pick_best_query(question: str, candidates: list[str], top_k: int = 1) -> list[dict]:
    """
    Rankeia queries candidatas usando modelo e heurísticas.
    
    Args:
        question: Pergunta em linguagem natural
        candidates: Lista de queries candidatas
        top_k: Número de queries a retornar
        
    Returns:
        Lista de dicionários com ranking das queries
    """
    normed = [normalize_sql(c) for c in candidates]
    pairs = [(question, q) for q in normed]
    model_scores = reranker_model.predict(pairs)
    rules = np.array([rule_score(q) for q in normed])
    final = 0.7 * model_scores + 0.3 * rules
    order = final.argsort()[::-1]
    ranking = [{
        "rank": i+1,
        "sql": candidates[idx],
        "norm_sql": normed[idx],
        "model_score": float(model_scores[idx]),
        "rule_score": float(rules[idx]),
        "final_score": float(final[idx])
    } for i, idx in enumerate(order[:top_k])]
    
    return ranking


def log_query_history(query_text: str, execution_time_ms: int, engine, plan_total_cost: float, plan_rows: int) -> None:
    """
    Salva o histórico da query executada na tabela metadata.query_history.
    
    Args:
        query_text: Texto da query executada.
        execution_time_ms: Tempo de execução em milissegundos.
        engine: SQLAlchemy engine já conectado ao banco.
        plan_total_cost: Custo total do plano de execução.
        plan_rows: Número de linhas do plano.
    """
    try:
        with engine.begin() as conn:
            db_user = conn.execute(text("SELECT current_user")).scalar()
            conn.execute(
                text("""
                    INSERT INTO metadata.query_history (query_text, execution_time_ms, plan_total_cost, plan_rows, db_user)
                    VALUES (:query_text, :execution_time_ms, :plan_total_cost, :plan_rows, :db_user)
                """),
                {"query_text": query_text, "execution_time_ms": execution_time_ms, "db_user": db_user, "plan_total_cost": plan_total_cost, "plan_rows": plan_rows}
            )
    except Exception as e:
        logger.error(f"Erro ao salvar histórico da query: {e}")
