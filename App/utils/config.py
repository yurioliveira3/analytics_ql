"""
Configurações da aplicação e inicialização de serviços.
"""

from langchain_postgres.vectorstores import DistanceStrategy
from langchain_huggingface import HuggingFaceEmbeddings
from pgvector.psycopg2 import register_vector
from langchain_postgres import PGVector
from sqlalchemy import create_engine
from dotenv import load_dotenv
from typing import Final
import sys
import os

# Adiciona o diretório raiz ao path para imports da Database
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# --- Constantes ---
DIR_PATH: Final[str] = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CONNECTION_STRING: Final[str | None] = os.environ.get("PG_CONNECTION_STRING")

if not CONNECTION_STRING:
    raise ValueError("A variável de ambiente PG_CONNECTION_STRING não foi definida.")

CONNECTION_STRING = (
    "postgresql+psycopg2://frontend_user:senha_forte@localhost:5482/analytics_db"
    "?options=-csearch_path%3Dlang,public"
)

# Modelo de embedding para o LangChain
# Usaremos um modelo open-source que performa bem para similaridade semântica.
embedding_function = HuggingFaceEmbeddings(
    model_name="BAAI/bge-large-en-v1.5"
)
dim = len(embedding_function.embed_query("probe"))  # 1024

engine = create_engine(CONNECTION_STRING)

with engine.connect() as conn:
    register_vector(conn.connection)

vector_store = PGVector(
    embeddings=embedding_function,
    connection=engine,
    collection_name="produtos", #TODO AJUSTAR PARA DEIXAR DINÂMICO
    embedding_length=1024,
    distance_strategy=DistanceStrategy.COSINE,
    pre_delete_collection=False,
    create_extension=True,
)
