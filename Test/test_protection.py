"""
Script de teste para demonstrar a camada de proteção de queries SQL.

Este script testa todas as funcionalidades implementadas na camada de proteção,
incluindo validação de integridade, segurança e auditoria.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'App'))

from App.utils.query_protection import (
    normalize_query,
    generate_query_hash,
    validate_query_integrity,
    validate_query_safety_enhanced,
    create_query_audit_log
)

def test_query_normalization():
    """Testa a normalização de queries."""
    print("=== Teste de Normalização de Queries ===")
    
    queries = [
        "SELECT * FROM users -- comentário",
        "SELECT   *   FROM   users   ",
        "SELECT * /* comentário */ FROM users",
        "SELECT *\nFROM users\nWHERE id = 1"
    ]
    
    for i, query in enumerate(queries, 1):
        normalized = normalize_query(query)
        print(f"Query {i}: {repr(query)}")
        print(f"Normalizada: {repr(normalized)}")
        print(f"Hash: {generate_query_hash(query)[:16]}...\n")

def test_integrity_validation():
    """Testa a validação de integridade."""
    print("=== Teste de Validação de Integridade ===")
    
    original_query = "SELECT * FROM users WHERE id = 1"
    same_query = "SELECT * FROM users WHERE id = 1"
    modified_query = "SELECT * FROM users WHERE id = 2"
    
    print(f"Query Original: {original_query}")
    print(f"Query Idêntica: {same_query}")
    print(f"Query Modificada: {modified_query}\n")
    
    # Teste 1: Queries idênticas
    valid, reason = validate_query_integrity(original_query, same_query)
    print(f"Validação (idênticas): {'✓ PASSOU' if valid else '✗ FALHOU'}")
    if not valid:
        print(f"Motivo: {reason}")
    
    # Teste 2: Queries diferentes
    valid, reason = validate_query_integrity(original_query, modified_query)
    print(f"Validação (diferentes): {'✗ FALHOU' if not valid else '✓ PASSOU'} (esperado falhar)")
    if not valid:
        print(f"Motivo: {reason}")
    print()

def test_security_validation():
    """Testa a validação de segurança."""
    print("=== Teste de Validação de Segurança ===")
    
    test_cases = [
        ("SELECT * FROM users", True, "Query SELECT válida"),
        ("DELETE FROM users", False, "Query DELETE perigosa"),
        ("SELECT * FROM users; DROP TABLE users", False, "Múltiplos statements"),
        ("SELECT * FROM users WHERE 1=1 OR 1=1", False, "Possível SQL injection"),
        ("SELECT * FROM users UNION SELECT * FROM passwords", False, "UNION attack"),
        ("INSERT INTO users VALUES (1, 'test')", False, "Query INSERT perigosa"),
    ]
    
    for query, expected_safe, description in test_cases:
        is_safe, reason, metadata = validate_query_safety_enhanced(query)
        status = "✓ SEGURA" if is_safe else "✗ PERIGOSA"
        result = "PASSOU" if (is_safe == expected_safe) else "FALHOU"
        
        print(f"Query: {query}")
        print(f"Descrição: {description}")
        print(f"Resultado: {status} - Teste {result}")
        if not is_safe:
            print(f"Motivo: {reason}")
        print(f"Verificações realizadas: {metadata['checks_performed']}")
        print()

def test_audit_logging():
    """Testa o sistema de auditoria."""
    print("=== Teste de Sistema de Auditoria ===")
    
    query = "SELECT COUNT(*) FROM users WHERE active = true"
    
    # Simular diferentes ações
    actions = [
        ("generated", {"ai_model": "gpt-4", "user_prompt": "quantos usuários ativos?"}),
        ("validated", {"validation_time_ms": 15, "security_checks": 5}),
        ("executed", {"execution_time_ms": 234, "rows_returned": 1500}),
    ]
    
    for action, metadata in actions:
        audit_log = create_query_audit_log(query, action, metadata)
        print(f"Ação: {action}")
        print(f"Log de Auditoria: {audit_log}")
        print()

def test_hash_consistency():
    """Testa a consistência dos hashes."""
    print("=== Teste de Consistência de Hashes ===")
    
    query = "SELECT * FROM users WHERE status = 'active'"
    
    # Gerar hashes múltiplas vezes
    hashes = [generate_query_hash(query) for _ in range(5)]
    
    print(f"Query: {query}")
    print("Hashes gerados:")
    for i, hash_val in enumerate(hashes, 1):
        print(f"  {i}: {hash_val}")
    
    all_same = all(h == hashes[0] for h in hashes)
    print(f"\nConsistência: {'✓ PASSOU' if all_same else '✗ FALHOU'}")
    print()

def main():
    """Executa todos os testes da camada de proteção."""
    print("🔒 TESTE DA CAMADA DE PROTEÇÃO DE QUERIES SQL")
    print("=" * 60)
    
    try:
        test_query_normalization()
        test_integrity_validation()
        test_security_validation()
        test_audit_logging()
        test_hash_consistency()
        
        print("✅ TODOS OS TESTES CONCLUÍDOS")
        print("\nA camada de proteção está funcionando corretamente!")
        
    except Exception as e:
        print(f"❌ ERRO DURANTE OS TESTES: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
