from utils.logger import get_logger
from utils.config import DIR_PATH
from utils.modules import (
    get_sql_from_text, 
    execute_sql_query, 
    is_query_safe, 
    suggest_chart, 
    generate_insights_payload,
    generative_model_insights, 
    read_prompt_file,
    safe_send_message,
    TRAD_ESTATISTICAS,
    ALGORITHM_MAPPING
)
from flask import Flask, render_template, request, session, redirect, url_for, make_response, jsonify
from flask_session import Session
import pandas as pd
import json
import io
import os
import uuid

# Importações do sistema de histórico
from Database.database import get_db
from Database.services import get_chat_service
from Database.models import chat_sessions

app = Flask(__name__)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = os.path.join(DIR_PATH, 'flask_session')
app.config['SESSION_PERMANENT'] = False

# Logger para este módulo
logger = get_logger(__name__)
Session(app)
app.secret_key = os.urandom(24)

def get_or_create_session_id() -> str:
    """Obtém o session_id atual, garante que existe no banco ou cria um novo."""
    if 'current_session_id' in session:
        db = next(get_db())
        try:
            sess_uuid = uuid.UUID(session['current_session_id'])
        except (ValueError, AttributeError):
            valid = False
        else:
            exists = (
                db.query(chat_sessions)
                .filter(
                    chat_sessions.id == sess_uuid,
                    chat_sessions.deleted == False
                )
                .first()
            )
            valid = bool(exists)
        if not valid:
            service = get_chat_service(db)
            session['current_session_id'] = service.create_session()
            session.modified = True
    else:
        db = next(get_db())
        service = get_chat_service(db)
        session['current_session_id'] = service.create_session()
        session.modified = True
    return session['current_session_id']

@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    """API para listar sessões de chat."""
    try:
        db = next(get_db())
        chat_service = get_chat_service(db)
        sessions = chat_service.get_sessions_list(limit=50)
        return jsonify({"sessions": sessions})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions/<session_id>", methods=["GET"])
def get_session_history(session_id: str):
    """API para obter histórico de uma sessão."""
    try:
        db = next(get_db())
        chat_service = get_chat_service(db)
        history = chat_service.get_session_history(session_id, limit=5)
        return jsonify({"history": history})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions/<session_id>/switch", methods=["POST"])
def switch_session(session_id: str):
    """API para trocar de sessão."""
    try:
        session['current_session_id'] = session_id
        session.modified = True
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions", methods=["POST"])
def create_new_session():
    """API para criar nova sessão."""
    try:
        data = request.get_json()
        title = data.get('title', None)
        
        db = next(get_db())
        chat_service = get_chat_service(db)
        new_session_id = chat_service.create_session(title)
        
        session['current_session_id'] = new_session_id
        session.modified = True
        
        return jsonify({"session_id": new_session_id})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id: str):
    """API para deletar sessão."""
    try:
        db = next(get_db())
        chat_service = get_chat_service(db)
        success = chat_service.delete_session(session_id)
        
        # Se deletou a sessão atual, cria uma nova
        if success and session.get('current_session_id') == session_id:
            new_session_id = chat_service.create_session()
            session['current_session_id'] = new_session_id
            session.modified = True
        
        return jsonify({"success": success})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/download_xlsx/<int:idx>')
def download_xlsx(idx: int):
    """
    Faz o download do resultado da execução em XLSX.
    Versão melhorada com tratamento robusto de erros e logs.
    """
    try:
        current_session_id = get_or_create_session_id()
        logger.debug(f"Download XLSX - Session ID: {current_session_id}, Index: {idx}")
        
        db = next(get_db())
        chat_service = get_chat_service(db)
        history_from_db = chat_service.get_session_history(current_session_id)
        
        logger.debug(f"Total messages in history: {len(history_from_db)}")
        
        # Converter para formato compatível e buscar pelo índice
        compatible_history = []
        for i, msg in enumerate(history_from_db):
            if msg["role"] == "assistant" and msg.get("execution_result"):
                exec_result = msg["execution_result"]
                
                # Tratar execution_result como string JSON se necessário
                if isinstance(exec_result, str):
                    try:
                        exec_result = json.loads(exec_result)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse execution_result as JSON at index {i}: {e}")
                        continue
                
                # Verificar se é dict e tem CSV
                if isinstance(exec_result, dict) and exec_result.get("csv"):
                    csv_content = exec_result.get("csv", "").strip()
                    if csv_content:  # Só adiciona se CSV não estiver vazio
                        compatible_history.append({
                            "csv": csv_content,
                            "ml_result": exec_result.get("ml_result"),
                            "total_rows": exec_result.get("total_rows", 0),
                            "original_index": i
                        })
                        logger.debug(f"Added to compatible_history: index {len(compatible_history)-1}, original {i}")
        
        logger.debug(f"Compatible history size: {len(compatible_history)}")
        
        # Validar índice
        if idx < 0 or idx >= len(compatible_history):
            logger.error(f"Invalid index {idx}. Valid range: 0 to {len(compatible_history)-1}")
            return jsonify({"error": f"Índice inválido. Resultados disponíveis: 0 a {len(compatible_history)-1}"}), 400
        
        # Obter dados do CSV
        csv_text = compatible_history[idx].get('csv', '').strip()
        if not csv_text:
            logger.error(f"Empty CSV content at index {idx}")
            return jsonify({"error": "Conteúdo CSV vazio para este índice"}), 400
        
        logger.debug(f"CSV length: {len(csv_text)} characters")
        
        # Converte CSV text em DataFrame com tratamento de erro
        try:
            df = pd.read_csv(io.StringIO(csv_text))
            logger.debug(f"DataFrame created successfully. Shape: {df.shape}")
        except Exception as e:
            logger.error(f"Failed to create DataFrame from CSV: {e}")
            return jsonify({"error": f"Erro ao processar dados CSV: {str(e)}"}), 500
        
        # Verificar se DataFrame não está vazio
        if df.empty:
            logger.error(f"Empty DataFrame at index {idx}")
            return jsonify({"error": "DataFrame vazio para este índice"}), 400
        
        # Adiciona coluna resultado_ml se disponível e compatível
        ml_res = compatible_history[idx].get("ml_result")
        if ml_res is not None:
            try:
                if len(ml_res) == len(df):
                    df["resultado_ml"] = ml_res
                    logger.debug(f"ML result column added successfully ({len(ml_res)} values)")
                else:
                    logger.warning(f"ML result length ({len(ml_res)}) doesn't match DataFrame length ({len(df)})")
            except Exception as e:
                logger.warning(f"Failed to add ML result column: {e}")
        
        # Gera XLSX em buffer com tratamento de erro
        try:
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name='Dados')
            output.seek(0)
            logger.debug(f"XLSX generated successfully. Buffer size: {len(output.getvalue())} bytes")
        except Exception as e:
            logger.error(f"Failed to generate XLSX: {e}")
            return jsonify({"error": f"Erro ao gerar arquivo Excel: {str(e)}"}), 500
        
        # Criar resposta com headers seguros
        try:
            response = make_response(output.read())
            filename = f"analytics_result_{idx}_{current_session_id[:8]}.xlsx"
            response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
            response.headers['Content-Type'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            response.headers['Content-Length'] = str(len(output.getvalue()))
            logger.debug(f"Response created successfully. Filename: {filename}")
            return response
        except Exception as e:
            logger.error(f"Failed to create response: {e}")
            return jsonify({"error": f"Erro ao criar resposta: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in download_xlsx: {e}")
        import traceback
        logger.error("Stack trace:", exc_info=True)
        return jsonify({"error": f"Erro interno do servidor: {str(e)}"}), 500

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Main route for the SQL generator.
    """
    # Verifica se é uma nova sessão
    is_new_session = request.args.get('new_session') == 'true'
    
    # Garantir que temos uma sessão ativa
    current_session_id = get_or_create_session_id()
    
    # Carregar histórico da sessão atual do banco (somente últimos 5)
    db = next(get_db())
    chat_service = get_chat_service(db)
    history_from_db = chat_service.get_session_history(current_session_id, limit=5)
    
    # Converter histórico do banco para formato compatível com template
    history = []
    for msg in history_from_db:
        if msg["role"] == "user":
            # Mensagem do usuário - aguarda mensagem do assistente
            user_entry = {
                'nl_query': msg["content"],
                'generated_query': None,
                'explanation': None,
                'used_tables': None,
                'ml_algorithm': None,
                'df_html': None,
                'dataframe_analysis': None,
                'ml_result': None,
                'insights': None
            }
            history.append(user_entry)
        elif msg["role"] == "assistant" and history:
            # Mensagem do assistente - completa o último entry do usuário
            last_entry = history[-1]
            
            # Parse do execution_result se for string JSON
            execution_result = msg.get("execution_result")
            if isinstance(execution_result, str):
                try:
                    execution_result = json.loads(execution_result)
                except:
                    execution_result = {}
            elif not isinstance(execution_result, dict):
                execution_result = {}
            
            last_entry.update({
                'generated_query': msg.get("generated_query"),
                'explanation': msg.get("explanation"),
                'used_tables': msg.get("used_tables"),
                'ml_algorithm': msg.get("ml_algorithm"),
                'insights': msg.get("insights"),
                'execution_time_ms': msg.get("execution_time_ms"),
                'total_cost': msg.get("total_cost"),
                'plan_rows': msg.get("plan_rows"),
                'chart_type': msg.get("chart_type"),
                'total_rows': execution_result.get("total_rows"),
                'csv': execution_result.get("csv"),
                'df_html': execution_result.get("df_html"),
                'dataframe_analysis': execution_result.get("dataframe_analysis"),
                'chart_html': execution_result.get("chart_html"),
                'ml_result': execution_result.get("ml_result")
            })
            
            # Marca como executada se tem resultados de execução
            if execution_result.get("df_html") or msg.get("execution_time_ms"):
                last_entry['executed_query'] = msg.get("generated_query")

    query = ""
    nl_query = ""  # Para manter a pergunta do usuário na caixa de texto

    # Se é uma nova sessão, força nl_query como vazio
    if is_new_session:
        nl_query = ""

    if request.method == "POST" and not is_new_session:
        natural_language_query = request.form.get("nl_query", "")
        
        if natural_language_query and natural_language_query.strip():
            # Salvar pergunta do usuário
            chat_service.save_user_message(current_session_id, natural_language_query)
            
            # Gerar SQL
            query, explanation, used_tables, ml_algorithm = get_sql_from_text(natural_language_query, db_name="PostgreSQL")
            
            # Salvar resposta inicial do assistente
            assistant_message_id = chat_service.save_assistant_message(
                current_session_id,
                content=f"Query SQL gerada para: {natural_language_query}",
                generated_query=query,
                explanation=explanation,
                used_tables=used_tables,
                ml_algorithm=ml_algorithm
            )
            
            # Adicionar ao histórico em memória para exibição imediata
            new_entry = {
                'nl_query': natural_language_query,
                'generated_query': query,
                'explanation': explanation,
                'used_tables': used_tables,
                'ml_algorithm': ml_algorithm,
                'df_html': None,
                'dataframe_analysis': None,
                'ml_result': None,
                'assistant_message_id': assistant_message_id  # Para atualizar depois
            }
            history.append(new_entry)
            nl_query = ""
        else:
            query = "-- Por favor, insira uma pergunta."
            nl_query = ""

    # Obter lista de sessões para sidebar
    sessions_list = chat_service.get_sessions_list(limit=50)
    
    # Extrair dados da última mensagem executada para exibir no template
    last_executed = None
    if history:
        # Procurar a última mensagem que foi executada
        for msg in reversed(history):
            if msg.get("executed", False) and msg.get("df_html"):
                last_executed = msg
                break
    
    # Preparar variáveis para o template
    template_vars = {
        "history": history,
        "nl_query": "" if (is_new_session or not history) else nl_query,  # Sempre vazio se nova sessão ou sem histórico
        "sessions": sessions_list,
        "current_session_id": current_session_id,
        "insights": "",
        "df_html": "",
        "dataframe_analysis": "",
        "total_rows": None,
        "csv": None
    }
    
    if last_executed:
        template_vars.update({
            "insights": last_executed.get("insights", ""),
            "df_html": last_executed.get("df_html", ""),
            "dataframe_analysis": last_executed.get("dataframe_analysis", ""),
            "total_rows": last_executed.get("total_rows"),
            "csv": last_executed.get("csv")
        })

    return render_template("index.html", **template_vars)

@app.route("/execute")
def execute_last_query():
    """
    Executa a última query gerada e salva no histórico persistente.
    """
    current_session_id = get_or_create_session_id()
    
    db = next(get_db())
    chat_service = get_chat_service(db)
    
    # Buscar a última mensagem do assistente da sessão atual
    history_from_db = chat_service.get_session_history(current_session_id, limit=5)
    
    last_assistant_message = None
    for msg in reversed(history_from_db):
        if msg["role"] == "assistant" and msg.get("generated_query"):
            last_assistant_message = msg
            break
    
    if not last_assistant_message:
        return redirect(url_for("index"))

    query = last_assistant_message.get('generated_query')
    
    if query and is_query_safe(query):
        exec_res, execution_time_ms, total_cost, plan_rows = execute_sql_query(query)
        
        result_data = {
            "execution_time_ms": execution_time_ms,
            "total_cost": total_cost,
            "plan_rows": plan_rows
        }
        
        df_html = None
        dataframe_analysis_html = None
        chart_html = None
        chart_type = None
        csv_text = ""

        if isinstance(exec_res, pd.DataFrame):
            # Registrar total de linhas e limitar exibição a 3 linhas
            total_rows = exec_res.shape[0]
            display_df = exec_res if total_rows <= 3 else exec_res.head(3)
            result_data["total_rows"] = total_rows
            
            # Análise descritiva apenas se existirem colunas numéricas
            numeric_df = exec_res.select_dtypes("number")
            if not numeric_df.empty:
                dataframe_analysis_df = (
                    numeric_df.describe(percentiles=[])
                    .transpose()[["count", "mean", "std", "min", "max"]]
                    .rename(columns=TRAD_ESTATISTICAS)
                    .round(2)
                )
                dataframe_analysis_df = dataframe_analysis_df.replace({pd.NA: "", float("nan"): ""})
                dataframe_analysis_html = dataframe_analysis_df.to_html(classes="dataframe", border=0)
                result_data["dataframe_analysis"] = dataframe_analysis_html
                
            # HTML do DataFrame limitado
            df_html = display_df.to_html(classes="dataframe", border=0, index=False)
            result_data["df_html"] = df_html
            
            # CSV do DataFrame completo para download
            csv_text = exec_res.to_csv(index=False)
            result_data["csv"] = csv_text
            
            # Sugere um gráfico
            chart_html, chart_type = suggest_chart(exec_res)
            # Garantir que as chaves existam mesmo sem gráfico proposto
            result_data["chart_html"] = chart_html or ""
            result_data["chart_type"] = chart_type or ""

            # Aplicar ML algorithm
            ml_algorithm = last_assistant_message.get('ml_algorithm')
            ml_result = None
            
            try:
                numeric_df = exec_res.select_dtypes(include=["number"]).dropna()
                if ml_algorithm and not numeric_df.empty:
                    alg_name = ml_algorithm.split("(")[0]
                    creator = ALGORITHM_MAPPING.get(alg_name)
                    if creator and not numeric_df.empty:
                        alg = creator()
                        if hasattr(alg, "fit_predict"):
                            ml_result = alg.fit_predict(numeric_df).tolist()
                        elif hasattr(alg, "predict"):
                            alg.fit(numeric_df)
                            ml_result = alg.predict(numeric_df).tolist()
                
                # Adiciona coluna com resultado do ML ao DataFrame se compatível
                if ml_result is not None and len(ml_result) == exec_res.shape[0]:
                    exec_res["resultado_ml"] = ml_result
                    result_data["ml_result"] = ml_result
                    
            except Exception as e:
                logger.error(f"Erro ao aplicar algoritmo de ML: {e}")

        else:
            # Se a execução retornou uma string de erro
            df_html = f'<div class="error-message">{exec_res}</div>'
            result_data["df_html"] = df_html
            # Sem gráfico para erro
            result_data["chart_html"] = ""
            result_data["chart_type"] = ""

        # Gerar insights
        payload = generate_insights_payload(
            last_entry=last_assistant_message,
            result=exec_res if isinstance(exec_res, pd.DataFrame) else None,
            dataframe_analysis_df=dataframe_analysis_df if "dataframe_analysis_df" in locals() else None,
            ml_algorithm=last_assistant_message.get('ml_algorithm'),
            chart_type=chart_type
        )

        prompt_template = read_prompt_file(os.path.join(DIR_PATH, "prompts", "insights_generation.txt"))
        prompt = prompt_template.replace("{payload}", json.dumps(payload, ensure_ascii=False, default=str))
        
        try:
            insights_resp = safe_send_message(generative_model_insights, prompt)
            insights = insights_resp.text
            result_data["insights"] = insights
        except Exception as e:
            insights = f"Erro ao gerar insights: {e}"
            result_data["insights"] = insights

        # Atualizar a mensagem do assistente no banco com os resultados da execução
        # Buscar a mensagem específica para atualizar
        from Database.models import chat_messages
        from sqlalchemy.orm import Session
        
        assistant_msg = (
            db.query(chat_messages)
            .filter(
                chat_messages.session_id == uuid.UUID(current_session_id),
                chat_messages.role == "assistant",
                chat_messages.generated_query == query
            )
            .order_by(chat_messages.created_at.desc())
            .first()
        )
        
        if assistant_msg:
            assistant_msg.execution_result = json.dumps(result_data, default=str)
            assistant_msg.execution_time_ms = execution_time_ms
            assistant_msg.total_cost = total_cost
            assistant_msg.plan_rows = plan_rows
            assistant_msg.chart_type = chart_type
            assistant_msg.insights = insights
            db.commit()

    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True, port=5001)
