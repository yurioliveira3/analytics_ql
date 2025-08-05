"""
Configurações centralizadas dos modelos LLM (Large Language Models).
Contém todas as instâncias e configurações dos modelos Gemini.
"""

import google.generativeai as genai
from dotenv import load_dotenv
from typing import Final
import os

# Carrega variáveis de ambiente
load_dotenv()

# --- Constantes ---
GEMINI_API_KEY: Final[str | None] = os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise ValueError("A variável de ambiente GEMINI_API_KEY não foi definida.")

# Configura a API Key do Gemini
genai.configure(api_key=GEMINI_API_KEY)

# --- Modelos Generativos Gemini ---

# Modelo para geração de consultas SQL
generative_model_sql = genai.GenerativeModel(
    model_name="gemini-2.0-flash-lite",  # Modelo mais leve, rápido e barato
    generation_config=genai.types.GenerationConfig(
        temperature=0.0,  # Controla o grau de aleatoriedade das respostas do modelo
        top_p=0.5,  # Limita a escolha dos próximos tokens aos mais prováveis
        top_k=60,  # Limita a escolha dos próximos tokens aos k mais prováveis
        max_output_tokens=1024,
        candidate_count=3,  # Número de respostas candidatas a serem geradas
        response_mime_type="application/json"
    ),
    system_instruction=(
        "Você é um especialista em SQL para PostgreSQL. "
        "Retorne SEMPRE um JSON válido seguindo o schema acordado. "
        "Nunca utilize aliases que formem termos ofensivos, constrangedores ou inadequados em português, inglês ou outros idiomas. "
        "Prefira abreviações neutras e profissionais."
    ),
)

# Modelo para geração de insights
generative_model_insights = genai.GenerativeModel(
    model_name="gemini-1.5-flash",  # Bom equilíbrio entre capacidade de raciocínio e custo
    generation_config=genai.types.GenerationConfig(
        temperature=0.2,
        top_p=0.9,
        top_k=70,
        max_output_tokens=512,
        candidate_count=1,
        response_mime_type="text/plain"
    ),
    system_instruction=(
        "Você é um especialista em análise de dados que gera insights de negócio "
        "com base num payload JSON. Seja sucinto e valide a consistência do JSON. "
        "Nunca utilize aliases que formem termos ofensivos, constrangedores ou inadequados em português, inglês ou outros idiomas. "
        "Prefira abreviações neutras e profissionais."
    ),
)

# Modelo para seleção de consultas (comentado, mas disponível para uso futuro)
# generative_model_picker = genai.GenerativeModel(
#     model_name="gemini-1.5-flash",
#     generation_config=genai.types.GenerationConfig(
#         temperature=0.0,
#         top_p=0.6,
#         top_k=15,
#         max_output_tokens=256,
#         candidate_count=1,
#         response_mime_type="application/json"
#     ),
#     system_instruction=(
#         "Você é um especialista em SQL que cria consultas otimizadas para o banco de dados PostgreSQL. "
#         "Sua tarefa é escolher a consulta SQL mais adequada entre as opções fornecidas."
#     )
# )
