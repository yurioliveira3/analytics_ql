#!/usr/bin/env python3
"""
Script para testar se a correção do prompt funcionou
"""

import os
import sys

# Adiciona o diretório pai ao path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Carrega variáveis de ambiente
from dotenv import load_dotenv
load_dotenv()

from utils.llm_factory import LLMFactory
import json

def test_query_direct():
    """Testa diretamente com o LLM"""
    
    print("=== TESTE DIRETO COM LLM ===")
    
    # Cria o modelo
    sql_model = LLMFactory.create_sql_model()
    print(f"✅ Modelo criado: {sql_model.config.model_name}")
    
    # Prompt simplificado para teste
    test_prompt = """
    Contexto: Você tem as tabelas:
    - alunos.disciplinas (id, nome, id_curso, id_professor)
    - alunos.cursos (id, nome, descricao)
    
    Pergunta: Contar o número de disciplinas por curso
    
    Retorne um JSON com sql_query para contar disciplinas agrupadas por curso.
    """
    
    print(f"Enviando prompt para {sql_model.config.model_name}...")
    print(f"Prompt: {test_prompt[:200]}...")
    
    try:
        response = sql_model.generate_content(test_prompt)
        print(f"\n✅ Resposta recebida:")
        print(f"Texto: {response.text}")
        
        # Tenta parsear como JSON
        try:
            parsed = json.loads(response.text)
            print(f"\n✅ JSON válido:")
            if 'sql_query' in parsed:
                print(f"SQL: {parsed['sql_query']}")
                if parsed.get('success', True):
                    print("🎉 SUCESSO - Query SQL gerada!")
                else:
                    print(f"❌ FALHA - {parsed.get('explanation', 'Sem explicação')}")
            else:
                print("⚠️  JSON sem sql_query")
        except json.JSONDecodeError:
            print("❌ Resposta não é JSON válido")
            
    except Exception as e:
        print(f"❌ Erro: {e}")

if __name__ == "__main__":
    test_query_direct()
