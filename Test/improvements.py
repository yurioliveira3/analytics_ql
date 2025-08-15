#!/usr/bin/env python3
"""
Testes para as melhorias no sistema de tratamento de saudações.
"""

import sys
import os

# Adiciona o diretório pai ao path para importar os módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from App.utils.first_layer import is_greeting_or_small_talk, is_vague_question, get_contextual_suggestions


def test_greeting_detection():
    """Testa a detecção de saudações."""
    print("=== Teste de Detecção de Saudações ===")
    
    greetings = [
        "oi",
        "olá",
        "bom dia",
        "boa tarde",
        "boa noite", 
        "hey",
        "hello",
        "obrigado",
        "valeu",
        "tchau",
        "até logo",
        "como vai",
        "tudo bem",
        "beleza",
        "hi there"
    ]
    
    non_greetings = [
        "quantos alunos estão matriculados",
        "qual a média de notas por disciplina",
        "mostrar presença dos alunos",
        "listar cursos disponíveis",
        "análise de desempenho dos estudantes"
    ]
    
    print("Testando saudações (devem retornar True):")
    for greeting in greetings:
        result = is_greeting_or_small_talk(greeting)
        print(f"'{greeting}' -> {result}")
    
    print("\nTestando não-saudações (devem retornar False):")
    for non_greeting in non_greetings:
        result = is_greeting_or_small_talk(non_greeting)
        print(f"'{non_greeting}' -> {result}")


def test_vague_question_detection():
    """Testa a detecção de perguntas vagas."""
    print("\n=== Teste de Detecção de Perguntas Vagas ===")
    
    vague_questions = [
        "me ajuda",
        "quero dados",
        "análise",
        "relatório",
        "informações",
        "mostre",
        "dashboard",
        "gráfico"
    ]
    
    specific_questions = [
        "quantos alunos têm nota acima de 8",
        "qual disciplina tem maior taxa de reprovação",
        "mostrar a média de presença por turma",
        "listar os 10 melhores alunos por nota",
        "análise de desempenho da disciplina de matemática"
    ]
    
    print("Testando perguntas vagas (devem retornar True):")
    for vague in vague_questions:
        result = is_vague_question(vague)
        print(f"'{vague}' -> {result}")
    
    print("\nTestando perguntas específicas (devem retornar False):")
    for specific in specific_questions:
        result = is_vague_question(specific)
        print(f"'{specific}' -> {result}")


def test_contextual_suggestions():
    """Testa a geração de sugestões contextuais."""
    print("\n=== Teste de Sugestões Contextuais ===")
    
    suggestions = get_contextual_suggestions()
    print(f"Número de sugestões retornadas: {len(suggestions)}")
    print("Sugestões geradas:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")


if __name__ == "__main__":
    try:
        test_greeting_detection()
        test_vague_question_detection()
        test_contextual_suggestions()
        print("\n🎉 Todos os testes executados com sucesso!")
        
    except Exception as e:
        print(f"\nErro durante os testes: {e}")
        import traceback
        traceback.print_exc()
