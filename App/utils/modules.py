"""
Módulos utilitários para processamento de dados e geração de consultas SQL.
"""

from utils.config import vector_store, DIR_PATH, embedding_function
from google.api_core.exceptions import ResourceExhausted
from sentence_transformers import CrossEncoder
from utils.llms import generative_model_sql, generative_model_insights
from sqlalchemy import create_engine, text
from utils.logger import get_logger
from typing import Final, Callable

import pandas as pd
import numpy as np
import sqlparse 
import json
import os
import re
import time

from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

import plotly.express as px
import plotly.io as pio
import uuid

# Logger para este módulo
logger = get_logger(__name__)

# Dicionário de tradução para análises estatísticas
TRAD_ESTATISTICAS = {
    "count": "contagem",
    "mean": "média",
    "std": "dv"
}

# Mapeamento de algoritmos de ML essenciais
ALGORITHM_MAPPING: dict[str, Callable] = {
    # Regressão: Previsão de valores contínos. Robusto e versátil.
    "RandomForestRegressor": RandomForestRegressor,
    # Classificação: Previsão de categorias. Ótimo para dados tabulares.
    "RandomForestClassifier": RandomForestClassifier,
    # Clusterização: Agrupamento de dados por similaridade. Padrão da indústria.
    "KMeans": KMeans,
    # Detecção de Anomalias: Identificação de outliers.
    "IsolationForest": IsolationForest,
    # Redução de Dimensionalidade: Projeção de dados para visualização.
    "PCA": lambda: PCA(n_components=2)
}

# Modelo para rankear a melhor query
reranker_model: Final = CrossEncoder("BAAI/bge-reranker-v2-m3", trust_remote_code=True)


def safe_send_message(model, prompt, history=None, retries=5, backoff_factor=2):
    """Envia uma mensagem ao modelo Gemini de forma segura."""
    attempt = 0
    while attempt < retries:
        try:
            response = model.generate_content(prompt)
            if history is not None:
                # O histórico agora pode armazenar o JSON diretamente
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
            logger.error(f"Erro inesperado ao enviar mensagem para o modelo: {e}", exc_info=True)
            break
    raise Exception("Máximo de tentativas atingido.")


def read_prompt_file(file_path: str) -> str:
    """Lê o conteúdo de um arquivo de prompt."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        # Fallback para o caso de o arquivo não ser encontrado no ambiente de execução
        return "Você é um especialista em SQL. Crie uma query para: {natural_language_query} com base em: {context}"


def is_query_safe(sql_query: str) -> bool:
    """Verifica se a query SQL é segura (read-only) para execução.

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
    """Normaliza o SQL retornado pelo modelo, removendo comentários e padronizando keywords.

    Args:
        q: Comando SQL a ser normalizado.

    Returns:
        SQL normalizado em uma única linha, keywords em maiúsculas.
    """
    q = sqlparse.format(q, strip_comments=True, keyword_case="upper", reindent=False)
    return " ".join(q.split())


import uuid
import plotly.express as px
import plotly.io as pio
import pandas as pd

def is_identifier(series: pd.Series) -> bool:
    name = series.name.lower()
    # 1) Nome suspeito
    if any(key in name for key in ["id", "cod", "code", "cpf", "rg", "registro"]):
        return True
    # 2) Cardinalidade alta e inteira
    if pd.api.types.is_integer_dtype(series):
        unique_ratio = series.nunique(dropna=True) / len(series)
        if unique_ratio >= 0.8:           # >= 80 % valores únicos
            return True
    if "data_nascimento" in name:
        return False 
    
    return False

def suggest_chart(df: pd.DataFrame) -> tuple[str | None, str | None]:
    """
    Analisa o DataFrame e devolve (html_snippet, chart_type).

    Retorna (None, None) se nenhuma regra encontrar gráfico adequado.
    """
    try:
        # 1 ─ Classificação de colunas
        num_cols = df.select_dtypes(include="number").columns.tolist()
        cat_cols = df.select_dtypes(exclude="number").columns.tolist()
        dt_cols  = df.select_dtypes(include=["datetime64[ns]", "datetimetz"]).columns.tolist()

        id_like  = [col for col in num_cols if is_identifier(df[col])]
        num_cols = [col for col in num_cols if col not in id_like]

        # ── Detecção de categorias de "baixa cardinalidade" ──────────────────
        CAT_SMALL_MAX = 8
        small_cat_cols = [c for c in cat_cols if df[c].nunique() <= CAT_SMALL_MAX]
        
        # ── Nova função: escolher categórica "melhor" (menor cardinalidade > 1) ──
        def get_best_categorical(cols: list[str]) -> str | None:
            """Retorna a categórica com menor cardinalidade > 1."""
            if not cols:
                return None
            valid_cols = [(c, df[c].nunique()) for c in cols if df[c].nunique() > 1]
            if not valid_cols:
                return None
            return min(valid_cols, key=lambda x: x[1])[0]

        # ── Filtro "all-unique" reativado ────────────────────────────────────────
        def has_all_unique_values(cols: list[str]) -> bool:
            """Verifica se todas as colunas categóricas têm apenas valores únicos."""
            return all(df[col].nunique() == len(df) for col in cols)

        if cat_cols and has_all_unique_values(cat_cols) and not num_cols:
            return None, None  # Pula gráfico se tudo for único

        # 2 ─ Regras específicas (mais restritas → mais genéricas)

        # 2A0. Pie para único registro com duas colunas numéricas (percentuais)
        if df.shape[0] == 1 and len(num_cols) == 2:
            values = df.iloc[0][num_cols].tolist()
            labels = num_cols
            fig = px.pie(
                values=values,
                names=labels,
                hole=0.3,
                labels={labels[0]: labels[0], labels[1]: labels[1]}
            )
            chart_type = "pizza"

        # 2A. Heatmap: 2 categóricas de baixa cardinalidade, 0 numéricas
        elif len(small_cat_cols) >= 2 and not num_cols:
            row, col = small_cat_cols[:2]
            pivot = pd.crosstab(df[row], df[col])
            fig = px.imshow(
                pivot,
                labels=dict(x=col, y=row, color="Contagem"),
                text_auto=True,
                aspect="auto"
            )
            chart_type = "mapa_de_calor"

        # 2B. Multi-line temporal: datetime + ≥2 numéricas
        elif dt_cols and len(num_cols) >= 2:
            time_col = dt_cols[0]
            plot_df = df[[time_col] + num_cols].sort_values(time_col)
            fig = px.line(plot_df, x=time_col, y=num_cols, markers=False)
            chart_type = "multilinha"

        # 2C. Linha temporal simples: datetime + 1 numérica
        elif dt_cols and len(num_cols) == 1:
            time_col = dt_cols[0]
            num_col = num_cols[0]
            plot_df = df[[time_col, num_col]].sort_values(time_col)
            fig = px.line(plot_df, x=time_col, y=num_col, markers=False)
            chart_type = "linha"

        # 2D. Bloco pie/bar unificado: 1 categórica + ≤1 numérica
        elif cat_cols and len(num_cols) <= 1:
            cat = get_best_categorical(cat_cols)
            if cat is None:
                return None, None  # Todas categóricas têm cardinalidade 1

            if num_cols:
                values_col = num_cols[0]
                counts = df[[cat, values_col]].dropna()
            else:
                values_col = "count"
                counts = df[cat].value_counts().reset_index()
                counts.columns = [cat, values_col]

            if len(counts) <= 4:
                fig = px.pie(counts, names=cat, values=values_col, hole=0.3)
                chart_type = "pizza"
            else:
                fig = px.bar(
                    counts.sort_values(values_col, ascending=False),
                    x=cat, y=values_col, text=values_col
                )
                chart_type = "barras"

        # 2E. Histograma: 1 numérica, 0 categóricas
        elif len(num_cols) == 1 and not cat_cols:
            fig = px.histogram(df, x=num_cols[0])
            chart_type = "histograma"

        # 2F. Scatter com performance otimizada: ≥2 numéricas
        elif len(num_cols) >= 2:
            WEBGL_THRESHOLD = 1000  # Acima de 1000 pontos usa WebGL
            render_mode = "webgl" if len(df) > WEBGL_THRESHOLD else "auto"
            
            fig = px.scatter(
                df, 
                x=num_cols[0], 
                y=num_cols[1],
                render_mode=render_mode
            )
            chart_type = "dispersao"

        # 2G. Fallback para categóricas restantes
        elif cat_cols:
            cat = get_best_categorical(cat_cols)
            if cat is None:
                return None, None
            
            counts = df[cat].value_counts().reset_index()
            counts.columns = [cat, "count"]
            fig = px.bar(counts, x=cat, y="count")
            chart_type = "barras-contagem"

        # 2H. Fallback para datetime sem numéricas
        elif dt_cols:
            dt = dt_cols[0]
            fig = px.histogram(df, x=dt)
            chart_type = "histograma-data"

        else:
            return None, None

        # 3 ─ Layout padrão e exportação
        fig.update_layout(width=1000, height=400, margin=dict(l=20, r=20, t=40, b=20))

        # Adiciona linha de tendência OLS quando aplicável
        add_trendline_if_applicable(fig, df, chart_type, num_cols, dt_cols)

        html = pio.to_html(
            fig,
            full_html=False,
            include_plotlyjs="cdn",
            div_id=f"plotly-{uuid.uuid4().hex}",
            config={
                "displaylogo": False,
                "modeBarButtonsToRemove": ["pan2d", "select2d", "lasso2d"]
            }
        )

        return html, chart_type

    except Exception as e:
        logger.error(f"Erro em suggest_chart: {e}")
        return None, None


def add_trendline_if_applicable(fig, df: pd.DataFrame, chart_type: str, num_cols: list[str], dt_cols: list[str]) -> None:
    """
    Acrescenta uma linha de tendência OLS quando:
      • chart_type == "dispersao"  -> usa as duas colunas numéricas
      • chart_type == "multilinha" -> usa o 1ª coluna numérica vs datetime
    A linha só é adicionada se R² >= R2_THRESHOLD.
    """
    R2_THRESHOLD = 0.20               # ajuste de sensibilidade

    try:
        # Caso 1 ─ Scatter: duas colunas numéricas
        if chart_type == "dispersao" and len(num_cols) >= 2:
            x_col, y_col = num_cols[:2]
            data = df[[x_col, y_col]].dropna()
            if len(data) < 2:
                return  # sem dados suficientes

            x = data[x_col].to_numpy()
            y = data[y_col].to_numpy()

        # Caso 2 ─ Multi-line temporal: datetime + numérico
        elif chart_type == "multilinha" and dt_cols and num_cols:
            time_col = dt_cols[0]
            y_col    = num_cols[0]     # tendência da 1ª série
            data = df[[time_col, y_col]].dropna()
            if len(data) < 2:
                return

            # Datetime → int64 (nanos) para regressão
            x = data[time_col].astype("int64") / 1e9     # segundos
            y = data[y_col].to_numpy()
        else:
            return  # não aplicável

        # Regressão OLS simples y = a*x + b
        slope, intercept = np.polyfit(x, y, 1)
        y_pred = slope * x + intercept
        denom = ((y - y.mean()) ** 2).sum()
        if denom == 0:
            return  # evita divisão por zero
        r2 = 1 - ((y - y_pred) ** 2).sum() / denom
        if np.isnan(r2) or r2 < R2_THRESHOLD:
            return  # tendência fraca

        # Adiciona linha de tendência
        x_min, x_max = x.min(), x.max()
        if chart_type == "dispersao":
            fig.add_scatter(
                x=[x_min, x_max],
                y=[intercept + slope*x_min, intercept + slope*x_max],
                mode="lines",
                line=dict(color="red", dash="dash"),
                name=f"Tendência (R²={r2:.2f})",
                hovertemplate=f"y = {slope:.2f}x + {intercept:.2f}<br>R² = {r2:.2f}<extra></extra>"
            )
        else:
            fig.add_scatter(
                x=pd.to_datetime([x_min*1e9, x_max*1e9]),
                y=[intercept + slope*x_min, intercept + slope*x_max],
                mode="lines",
                line=dict(color="red", dash="dash"),
                name=f"Tendência (R²={r2:.2f})",
                hovertemplate=f"y = {slope:.2f}x + {intercept:.2f}<br>R² = {r2:.2f}<extra></extra>"
            )
    except Exception as e:
        logger.error(f"Erro em add_trendline_if_applicable: {e}")


def rule_score(sql: str, forbidden: tuple[str, ...] = ("DELETE","UPDATE","INSERT","ALTER"), penalize_star: bool = True) -> float:
    """Calcula heurística simples para consultas SQL."""
    s = 1.0
    up = sql.upper()
    if any(f in up for f in forbidden):
        return 0.0
    if penalize_star and "SELECT *" in up:
        s -= 0.1
    return max(0.0, s)


def pick_best_query(question: str, candidates: list[str], top_k: int = 1) -> list[dict]:
    """Rankeia queries candidatas usando modelo e heurísticas."""
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

def get_sql_from_text(natural_language_query: str, db_name: str) -> tuple[str, str, list[str], str]:
    """
    Gera uma consulta SQL a partir de uma pergunta em linguagem natural.

    1.  Busca metadados relevantes no banco vetorial (PGVector).
    2.  Monta um contexto com os metadados encontrados.
    3. Gera uma consulta SQL a partir de uma pergunta em linguagem natural em duas etapas:
        3.1. Gera 3 consultas SQL candidatas usando o Gemini.
        3.2. Usa o Gemini novamente para selecionar a melhor consulta entre as candidatas.

    Returns:
        Tuple contendo a query SQL, explicação e lista de tabelas usadas.
    """
    # 1. Busca por similaridade no PGVector
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
        return "-- Nenhum metadado relevante encontrado para a pergunta.", "", []

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
        
        if not response.candidates:
            return "-- Nenhuma query válida foi gerada.", "", [], ""

        sql_candidates = []
        ml_algorithms = []
        used_tables_list = []
        explanations = []  # Lista de explicações por candidato
        for candidate in response.candidates:
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


def log_query_history(query_text: str, execution_time_ms: int, engine, plan_total_cost: float, plan_rows: int) -> None:
    """
    Salva o histórico da query executada na tabela metadata.query_history.
    Args:
        query_text: Texto da query executada.
        execution_time_ms: Tempo de execução em milissegundos.
        engine: SQLAlchemy engine já conectado ao banco.
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


def generate_insights_payload(last_entry: dict, result: pd.DataFrame | str, dataframe_analysis_df: pd.DataFrame | None = None, ml_algorithm: str | None = None, chart_type: str | None = None) -> dict:
    """Monta o payload JSON para geração de insights.

    Args:
        last_entry: Última entrada do histórico da sessão.
        result: Resultado da execução da query (DataFrame ou erro).
        dataframe_analysis_df: DataFrame com análise descritiva (opcional).

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
        "chart_type": chart_type if chart_type else "Nenhum gráfico sugerido"
    }
    
    return payload
