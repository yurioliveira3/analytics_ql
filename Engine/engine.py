# c:\projects\Analytics_IA\Backend\engine.py
from config.setup import genai, ResourceExhausted, DB_DSN, DIR, setup_logging, get_ambiente_dinamico
from lang.chain import get_or_create_collection, insert_objects
from psycopg.rows import dict_row
from datetime import datetime
import logging
import psycopg
import time
import json

def configurar_modelo() -> genai.GenerativeModel:
    """
    Configura e retorna uma instância do modelo generativo Gemini com parâmetros específicos.

    Retorna:
        genai.GenerativeModel: Instância configurada do modelo generativo.

    Lança:
        Exception: Caso ocorra algum erro durante a configuração do modelo.

    Detalhes:
        - Utiliza o modelo "gemini-2.0-flash".
        - Define os parâmetros de geração:
            - temperature: controla a aleatoriedade das respostas
            - top_p: probabilidade acumulada para amostragem
            - top_k: considera os "x" tokens mais prováveis
            - max_output_tokens: número máximo de tokens na resposta
            - candidate_count: número de respostas candidatas a serem geradas
            - response_mime_type: tipo de resposta (text/plain ou application/json)
        - Em caso de erro, registra no logger e relança a exceção.

        - Para respostas técnicas e objetivas, use temperature baixo, top_p e top_k moderados.
        - Para criatividade, aumente temperature, top_p e/ou top_k.
    """
    """Configura e retorna o modelo generativo com os parâmetros adequados."""
    try:
        # O response_mime_type="application/json" instrui o modelo a sempre retornar JSON.
        modelo = genai.GenerativeModel(
            model_name="gemini-2.0-flash-lite", #Modelo mais leve, rápido e barato.
            generation_config=genai.types.GenerationConfig(
                temperature=0.05, #Controla o grau de aleatoriedade das respostas do modelo.
                top_p=0.6, #Limita a escolha dos próximos tokens aos mais prováveis, até que a soma das probabilidades atinja o valor de top_p
                top_k=40,  #Limita a escolha dos próximos tokens aos k mais prováveis.
                max_output_tokens=2048,
                candidate_count=1,
                response_mime_type="application/json"
            )
        )
        return modelo
    except Exception as e:
        logging.error(f"Erro ao instanciar modelo: {e}")
        raise

# --- Funções de Extração de DDL para PostgreSQL ---

def get_table_ddl(conn, schema_name, table_name):
    """Gera o DDL para uma tabela específica no PostgreSQL."""
    ddl = []
    with conn.cursor() as cur:
        # Definição das colunas
        cur.execute("""
            SELECT column_name, data_type, character_maximum_length, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_schema = %s AND table_name = %s
            ORDER BY ordinal_position;
        """, (schema_name, table_name))
        columns = cur.fetchall()
        
        col_defs = []
        for col in columns:
            col_def = f'    "{col[0]}" {col[1]}'
            if col[2]:
                col_def += f'({col[2]})'
            if col[3] == 'NO':
                col_def += ' NOT NULL'
            if col[4]:
                col_def += f' DEFAULT {col[4]}'
            col_defs.append(col_def)
        
        ddl.append(f'CREATE TABLE {schema_name}.{table_name} (\n' + ',\n'.join(col_defs))

        # Constraints (PK, FK, UNIQUE, CHECK)
        cur.execute("""
            SELECT conname, pg_get_constraintdef(oid) as condef
            FROM pg_constraint
            WHERE conrelid = %s::regclass;
        """, (f'"{schema_name}"."{table_name}"',))
        constraints = cur.fetchall()
        if constraints:
            ddl.append(',\n' + ',\n'.join([f'    CONSTRAINT "{c[0]}" {c[1]}' for c in constraints]))

        ddl.append('\n);')

        # Índices
        cur.execute("""
            SELECT indexdef FROM pg_indexes WHERE schemaname = %s AND tablename = %s;
        """, (schema_name, table_name))
        indexes = cur.fetchall()
        for index in indexes:
            # Evita duplicar o índice da PK
            if 'CREATE UNIQUE INDEX' not in index[0]:
                 ddl.append(f"\n{index[0]}")

    return "\n".join(ddl)

def get_view_ddl(conn, schema_name, view_name):
    """Obtém o DDL de uma VIEW."""
    with conn.cursor() as cur:
        cur.execute("SELECT definition FROM pg_views WHERE schemaname = %s AND viewname = %s;", (schema_name, view_name))
        result = cur.fetchone()
        return f"CREATE OR REPLACE VIEW {schema_name}.{view_name} AS\n{result[0]}" if result else ""

def get_function_ddl(conn, schema_name, function_name):
    """Obtém o DDL de uma FUNCTION ou PROCEDURE."""
    with conn.cursor() as cur:
        # pg_get_functiondef precisa do OID da função
        cur.execute("""
            SELECT p.oid
            FROM pg_proc p
            JOIN pg_namespace n ON n.oid = p.pronamespace
            WHERE n.nspname = %s AND p.proname = %s;
        """, (schema_name, function_name))
        oid = cur.fetchone()
        if oid:
            cur.execute("SELECT pg_get_functiondef(%s);", (oid[0],))
            return cur.fetchone()[0]
        return ""

def get_materialized_view_ddl(conn, schema_name: str, view_name: str) -> str:
    """Obtém o DDL de uma MATERIALIZED VIEW."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT definition FROM pg_matviews WHERE schemaname = %s AND matviewname = %s;",
            (schema_name, view_name),
        )
        result = cur.fetchone()
        return (
            f"CREATE MATERIALIZED VIEW {schema_name}.{view_name} AS\n{result[0]}"
            if result
            else ""
        )


def get_trigger_ddl(conn, schema_name: str, trigger_name: str) -> str:
    """Obtém o DDL de um TRIGGER."""
    with conn.cursor() as cur:
        cur.execute(
            "SELECT pg_get_triggerdef(oid) FROM pg_trigger WHERE tgname = %s;",
            (trigger_name,),
        )
        # Nota: Triggers não são associados a schemas diretamente em pg_trigger,
        # a busca é pelo nome, que se espera ser único no contexto desejado.
        result = cur.fetchone()
        return result[0] if result else ""


def get_all_objects_ddl(conn, schema_name):
    """Busca todos os objetos de um schema e retorna seus metadados e DDLs."""
    objects_list = []
    with conn.cursor(row_factory=dict_row) as cur:
        # Tabelas e Views
        cur.execute("""
            SELECT table_name as name, table_type as type FROM information_schema.tables 
            WHERE table_schema = %s AND table_type IN ('BASE TABLE', 'VIEW')
        """, (schema_name,))
        db_objects = cur.fetchall()

        # Funções
        cur.execute("""
            SELECT routine_name as name, 'FUNCTION' as type FROM information_schema.routines 
            WHERE specific_schema = %s
        """, (schema_name,))
        db_objects.extend(cur.fetchall())

    total_objects = len(db_objects)
    logger.info(f"Encontrados {total_objects} objetos no schema '{schema_name}'.")

    for i, obj in enumerate(db_objects, 1):
        obj_name = obj['name']
        obj_type = obj['type']
        logger.info(f"[{i}/{total_objects}] Extraindo DDL para: {obj_name} ({obj_type})")
        
        ddl = ""
        try:
            if obj_type == 'BASE TABLE':
                ddl = get_table_ddl(conn, schema_name, obj_name)
            elif obj_type == 'VIEW':
                ddl = get_view_ddl(conn, schema_name, obj_name)
            elif obj_type == 'FUNCTION':
                ddl = get_function_ddl(conn, schema_name, obj_name)
            
            if ddl:
                # Mock de metadados, já que a extração detalhada (linhas, etc.) é complexa
                objects_list.append({
                    "Objeto": obj_name,
                    "Tipo": obj_type,
                    "ddl": ddl,
                    "Dependentes": "N/A",
                    "Dependências": "N/A",
                    "Linhas": "N/A",
                    "Status": "N/A",
                    "Created": "N/A"
                })
        except Exception as e:
            logger.error(f"Falha ao extrair DDL para {obj_name}: {e}")

    return objects_list

# --- Funções Principais do Engine (adaptadas) ---

def file_open(file_path):
    """Abre e lê o conteúdo de um arquivo."""
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

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

def summarize_ddl(model, ddl_text: str, chat_history, db_name: str = "PostgreSQL", *, descrever_colunas: bool = True):
    """Gera um resumo do DDL de um objeto, esperando uma resposta JSON."""
    initial_prompt = file_open(f"{DIR}\\config\\prompts\\prompt_ddl.txt").replace("{db_name}", db_name)
    
    instrucao_colunas = "" if descrever_colunas else '\n\nInstrução Adicional: Ignore a tarefa de descrever colunas. Retorne a chave "colunas" como uma lista vazia [].'
    ddl_prompt = f"DDL:\n{ddl_text}".strip()

    try:
        response = safe_send_message(model, initial_prompt + "\n" + ddl_prompt + instrucao_colunas, chat_history)
        
        # Como o mime_type é application/json, o 'text' já é a string JSON.
        data = json.loads(response.text)
        
        return data.get("resumo", "Resumo indisponível"), str(data.get("complexidade", "0")), data.get("colunas", [])
    
    except json.JSONDecodeError as e:
        logger.error(f"Erro ao decodificar JSON da resposta do modelo: {e}\nResposta recebida:\n{response.text}")
        return "Erro ao processar resposta JSON", "-1", []
    except Exception as e:
        logger.error(f"Erro ao processar DDL com a IA: {e}")
        return "Erro ao gerar resumo", "-1", []

def schema_summary(model, schema_name, summary_data, chat_history):
    """Gera um resumo do schema, esperando uma resposta JSON."""
    initial_prompt = file_open(f"{DIR}\\config\\prompts\\prompt_summary.txt")
    
    try:
        response = safe_send_message(model, initial_prompt + "\n" + summary_data, chat_history)
        data = json.loads(response.text)
        resume = data.get("resumo_schema", "Resumo do schema indisponível.")
        logger.info(f"Resumo gerado para o schema '{schema_name}'.")
        return resume
    except Exception as e:
        logger.error(f"Erro ao gerar resumo do schema '{schema_name}': {e}")
        return "Erro ao gerar resumo do schema."

def get_objects_metadata(conn, schema_name: str) -> list[dict]:
    """
    Busca todos os objetos de um schema usando a query avançada 
    e retorna seus metadados.
    """
    try:
        query = file_open(f"{DIR}\\config\\queries\\objetos_schema.sql")
       
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(query, (schema_name,))
            objects = cur.fetchall()
            logger.info(f"Encontrados {len(objects)} objetos com metadados avançados no schema '{schema_name}'.")
            return objects
    except Exception as e:
        logger.error(f"Erro ao executar a query de metadados para o schema {schema_name}: {e}")
        return []

def contar_tokens(texto: str) -> int:
    """
    Estima o número de tokens em um texto para modelos Gemini.
    Aproximação: 1 token ≈ 4 caracteres (padrão OpenAI/Gemini).

    Args:
        texto: Texto a ser analisado.

    Returns:
        Número estimado de tokens.
    """
    return max(1, len(texto) // 4)

def processar_schema(model: genai.GenerativeModel, conn, schema_name: str) -> tuple[list[dict], str, int, int]:
    """
    Processa todos os objetos de um schema, enriquece com metadados,
    gera resumos com IA e retorna os dados e contagem de tokens.

    Returns:
        processed_data: Lista de objetos processados.
        schema_resume: Resumo do schema.
        total_tokens_enviados: Total de tokens enviados para o modelo.
        total_tokens_recebidos: Total de tokens recebidos do modelo.
    """
    objects_with_metadata = get_objects_metadata(conn, schema_name)

    processed_data: list[dict] = []
    chat_history: list[dict] = []
    summary_concat: str = ""
    total_tokens_enviados: int = 0
    total_tokens_recebidos: int = 0

    if not objects_with_metadata:
        logger.warning(f"Nenhum objeto encontrado para o schema {schema_name} pela query de metadados.")
        return [], "", 0, 0

    for i, obj_meta in enumerate(objects_with_metadata, 1):
        try:
            obj_name = obj_meta['object_name']
            obj_type = obj_meta['object_type']

            logger.info(f"[{i}/{len(objects_with_metadata)}] Processando: {obj_name} ({obj_type})")

            ddl = ""
            if obj_type == 'TABLE':
                ddl = get_table_ddl(conn, schema_name, obj_name)
            elif obj_type == 'VIEW':
                ddl = get_view_ddl(conn, schema_name, obj_name)
            elif obj_type in ('FUNCTION', 'PROCEDURE'):
                ddl = get_function_ddl(conn, schema_name, obj_name)
            elif obj_type == 'MATERIALIZED VIEW':
                ddl = get_materialized_view_ddl(conn, schema_name, obj_name)
            elif obj_type == 'TRIGGER':
                ddl = get_trigger_ddl(conn, schema_name, obj_name)

            if not ddl:
                logger.warning(f"Não foi possível obter DDL para {obj_name}, revise se o tipo do objeto está mapeado!")
                continue

            obj_meta['ddl'] = ddl

            descrever_colunas_flag = obj_type == "TABLE"
            prompt = file_open(f"{DIR}\\config\\prompts\\prompt_ddl.txt").replace("{db_name}", "PostgreSQL") + "\n" + f"DDL:\n{ddl}".strip()
            if not descrever_colunas_flag:
                prompt += '\n\nInstrução Adicional: Ignore a tarefa de descrever colunas. Retorne a chave "colunas" como uma lista vazia [].'

            total_tokens_enviados += contar_tokens(prompt)

            summary, complexity, columns = summarize_ddl(
                model, ddl, chat_history, descrever_colunas=descrever_colunas_flag
            )

            # Soma tokens recebidos (resposta do modelo)
            if isinstance(summary, str):
                total_tokens_recebidos += contar_tokens(summary)
            if isinstance(columns, list):
                total_tokens_recebidos += sum(contar_tokens(str(col)) for col in columns)

            obj_meta["resumo"] = summary
            obj_meta["complexidade"] = complexity
            obj_meta["colunas"] = columns

            processed_data.append(obj_meta)
            summary_concat += f"{obj_name} ({obj_type}) - {summary}\n"

        except Exception as e:
            logger.error(f"Erro ao processar o objeto {obj_name} ({obj_type}): {e}", exc_info=True)

    schema_resume = schema_summary(model, schema_name, summary_concat, chat_history)
    total_tokens_recebidos += contar_tokens(schema_resume)

    return processed_data, schema_resume, total_tokens_enviados, total_tokens_recebidos

def main() -> None:
    """Executa o fluxo completo de mapeamento do banco de dados PostgreSQL."""
    global logger
    logger = setup_logging("postgres_mapper", "back_app")
    hora_inicio = datetime.now()

    try:
        model = configurar_modelo()
        ambiente = get_ambiente_dinamico()
        logger.info(f"INICIANDO MAPEAMENTO DO BANCO DE DADOS POSTGRESQL NO AMBIENTE {ambiente}")

        with psycopg.connect(DB_DSN) as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT schema_name FROM information_schema.schemata
                    WHERE schema_name NOT IN ('pg_toast', 'pg_catalog', 'information_schema', 'lang', 'public')
                    AND schema_name NOT LIKE 'pg_temp_%%';
                """)
                schemas_to_process = [row[0] for row in cur.fetchall()]

            logger.info(f"Schemas a serem processados: {schemas_to_process}")

            for schema in schemas_to_process:
                logger.info(f"--- INICIANDO PROCESSAMENTO DO SCHEMA: {schema} ---")

                processed_objects, schema_resume, tokens_enviados, tokens_recebidos = processar_schema(model, conn, schema)

                logger.info(f"Tokens  [Enviados: {tokens_enviados} | Recebidos: {tokens_recebidos}]")

                if processed_objects:
                    collection_id = get_or_create_collection(schema, schema_resume)
                    insert_objects(collection_id, processed_objects)
                    logger.info(f"Dados do schema '{schema}' persistidos com sucesso.")
                else:
                    logger.warning(f"Nenhum dado processado para o schema '{schema}'.")

    except psycopg.OperationalError as e:
        logger.error(f"Erro de conexão com o PostgreSQL: {e}. Verifique se o container está no ar e as credenciais estão corretas.")
    except Exception as e:
        logger.error(f"Erro fatal durante a execução: {e}", exc_info=True)
    finally:
        hora_fim = datetime.now()
        tempo_total = round((hora_fim - hora_inicio).total_seconds(), 0)
        logger.info(f"MAPEAMENTO FINALIZADO. Tempo total: {tempo_total} segundos.")

if __name__ == "__main__":
    main()