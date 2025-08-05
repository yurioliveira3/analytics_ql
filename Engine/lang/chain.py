# c:\projects\Analytics_IA\Backend\lang\chain.py
from langchain_huggingface import HuggingFaceEmbeddings
from config.setup import DB_DSN
from uuid import uuid4
import logging
import psycopg
import json

logger = logging.getLogger(__name__)

"""
    Instancia o modelo de embedding que gera vetores de 1024 dimensões
    
    Prós:
        Qualidade: Este modelo é projetado para oferecer alta precisão, e suas 1024 dimensões são parte do que o torna eficaz em entender contextos técnicos complexos. Para a sua finalidade de mapear e consultar metadados de banco de dados, a precisão é crucial.
    Contras:
        Performance: Exige um pouco mais de recursos computacionais e de armazenamento em comparação com a versão de 768 dimensões.
"""
embedding_model = HuggingFaceEmbeddings(model_name="BAAI/bge-large-en-v1.5")

def get_or_create_collection(schema_name: str, schema_summary: str) -> str:
    """
    Verifica se uma collection para o schema existe. Se não, cria uma nova.
    Atualiza o metadado com o resumo do schema.
    Retorna o UUID da collection.
    """
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT uuid FROM lang.langchain_pg_collection WHERE name = %s",
                (schema_name,)
            )
            result = cur.fetchone()
            cmetadata = json.dumps({"resumo_schema": schema_summary})

            if result:
                collection_uuid = result[0]
                cur.execute(
                    "UPDATE lang.langchain_pg_collection SET cmetadata = %s WHERE uuid = %s",
                    (cmetadata, collection_uuid)
                )
                logger.info(f"Metadado da collection '{schema_name}' atualizado.")
                return collection_uuid
            else:
                collection_uuid = uuid4()
                cur.execute(
                    "INSERT INTO lang.langchain_pg_collection (uuid, name, cmetadata) VALUES (%s, %s, %s)",
                    (collection_uuid, schema_name, cmetadata)
                )
                logger.info(f"Collection '{schema_name}' criada com UUID: {collection_uuid}")
                return collection_uuid


def insert_objects(collection_id: str, objects_data: list[dict]) -> None:
    """
    Gera embeddings e insere os metadados ricos dos objetos do schema
    na tabela de embeddings.
    """
    with psycopg.connect(DB_DSN) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM lang.langchain_pg_embedding WHERE collection_id = %s",
                (collection_id,),
            )
            logger.info(
                f"Registros antigos da collection UUID {collection_id} foram limpos."
            )

            for obj in objects_data:
                # Concatena resumo e DDL para formar o documento
                document_content = (
                    f"Resumo: {obj.get('resumo', '')}\n\nDDL:\n{obj.get('ddl', '')}"
                )

                # Gera o embedding para o documento usando HuggingFace
                embedding = embedding_model.embed_query(document_content)

                cur.execute(
                    """
                    INSERT INTO lang.langchain_pg_embedding
                        (uuid, collection_id, embedding, document, cmetadata, custom_id)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        uuid4(),
                        collection_id,
                        embedding,
                        document_content,
                        # Mapeia todos os novos metadados para o JSONB
                        json.dumps(
                            {
                                "tipo": obj.get("object_type"),
                                "resumo": obj.get("resumo"),
                                "complexidade": obj.get("complexidade"),
                                "colunas": obj.get("colunas", []),
                                "dependentes_cont": obj.get("depend"),
                                "dependencias_cont": obj.get("dependencies"),
                                "lista_dependentes": obj.get("depend_list"),
                                "lista_dependencias": obj.get("dependencies_list"),
                                "fks": obj.get("fks"),
                                "fks_externas": obj.get("fks_externas"),
                                "linhas": obj.get("linhas"),
                                "tamanho_mb": float(obj.get("tamanho_mb", 0.0)),
                                "indices": obj.get("indexes"),
                                "triggers": obj.get("triggers"),
                                "status": obj.get("status"),
                                "data_criacao": obj.get("created", "").isoformat()
                                if obj.get("created")
                                else None,
                                "data_ultima_ddl": obj.get(
                                    "last_ddl_time", ""
                                ).isoformat()
                                if obj.get("last_ddl_time")
                                else None,
                            }
                        ),
                        obj.get("object_name"),
                    ),
                )
            logger.info(
                f"{len(objects_data)} objetos inseridos na collection UUID {collection_id}."
            )