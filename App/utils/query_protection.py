"""
Utilitários para proteção e validação de integridade de queries SQL.

Este módulo fornece funções para garantir que a query executada seja
exatamente a mesma que foi gerada e aprovada pelo usuário.
"""

import re
import hashlib
from typing import Tuple
from .logger import get_logger

logger = get_logger(__name__)


def normalize_query(query: str) -> str:
    """
    Normaliza uma query SQL para comparação consistente.
    Remove comentários, espaços extras e padroniza o formato.
    
    Args:
        query: Query SQL a ser normalizada
        
    Returns:
        Query normalizada
    """
    if not query:
        return ""
    
    # Remove comentários de linha (--) 
    query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
    
    # Remove comentários de bloco (/* */)
    query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
    
    # Remove espaços extras e quebras de linha
    query = ' '.join(query.split())
    
    # Converte para minúsculas para comparação
    return query.strip().lower()


def generate_query_hash(query: str) -> str:
    """
    Gera um hash SHA-256 da query normalizada para verificação de integridade.
    
    Args:
        query: Query SQL original
        
    Returns:
        Hash SHA-256 em hexadecimal
    """
    normalized = normalize_query(query)
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest()


def validate_query_integrity(stored_query: str, execution_query: str) -> Tuple[bool, str]:
    """
    Valida se a query armazenada é exatamente a mesma que será executada.
    
    Args:
        stored_query: Query armazenada no banco
        execution_query: Query que será executada
        
    Returns:
        Tupla (é_válida, motivo_se_inválida)
    """
    if not stored_query or not execution_query:
        return False, "Query vazia detectada"
    
    stored_hash = generate_query_hash(stored_query)
    execution_hash = generate_query_hash(execution_query)
    
    if stored_hash != execution_hash:
        logger.warning(
            f"Integridade da query comprometida. "
            f"Hash armazenado: {stored_hash[:16]}..., "
            f"Hash execução: {execution_hash[:16]}..."
        )
        return False, "Query foi modificada após geração"
    
    return True, ""


def create_query_audit_log(query: str, action: str, metadata: dict = None) -> dict:
    """
    Cria um registro de auditoria para ações relacionadas à query.
    
    Args:
        query: Query SQL
        action: Ação realizada (ex: 'generated', 'validated', 'executed')
        metadata: Metadados adicionais
        
    Returns:
        Dicionário com informações de auditoria
    """
    from datetime import datetime
    
    audit_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "query_hash": generate_query_hash(query),
        "query_length": len(query),
        "action": action,
        "normalized_query": normalize_query(query)[:100] + "..." if len(normalize_query(query)) > 100 else normalize_query(query)
    }
    
    if metadata:
        audit_record.update(metadata)
    
    return audit_record


def validate_query_safety_enhanced(query: str) -> Tuple[bool, str, dict]:
    """
    Validação de segurança aprimorada para queries SQL.
    Inclui verificações adicionais além das básicas.
    
    Args:
        query: Query SQL a ser validada
        
    Returns:
        Tupla (é_segura, motivo_se_não_segura, metadados_validação)
    """
    validation_metadata = {
        "query_length": len(query),
        "query_hash": generate_query_hash(query),
        "checks_performed": []
    }
    
    if not query or not query.strip():
        return False, "Query vazia ou apenas espaços", validation_metadata
    
    # Verificação de palavras-chave perigosas (case-insensitive)
    DANGEROUS_KEYWORDS = [
        "INSERT", "UPDATE", "DELETE", "DROP", "TRUNCATE", 
        "ALTER", "CREATE", "GRANT", "REVOKE", "MERGE",
        "EXECUTE", "EXEC", "CALL"
    ]
    
    normalized = normalize_query(query)
    validation_metadata["checks_performed"].append("dangerous_keywords")
    
    for keyword in DANGEROUS_KEYWORDS:
        if re.search(r'\b' + keyword.lower() + r'\b', normalized):
            return False, f"Palavra-chave perigosa detectada: {keyword}", validation_metadata
    
    # Verificação de tentativas de SQL injection comuns
    injection_patterns = [
        r';.*--',  # Terminação de statement seguida de comentário
        r'union\s+select',  # UNION SELECT attacks
        r'or\s+1\s*=\s*1',  # OR 1=1 attacks
        r'and\s+1\s*=\s*1',  # AND 1=1 attacks
        r'\'.*or.*\'.*=.*\'',  # Quote-based injection
    ]
    
    validation_metadata["checks_performed"].append("injection_patterns")
    
    for pattern in injection_patterns:
        if re.search(pattern, normalized, re.IGNORECASE):
            return False, f"Padrão suspeito de SQL injection detectado", validation_metadata
    
    # Verificação de múltiplos statements
    if ';' in query.rstrip(';'):  # Permite apenas um ; no final
        validation_metadata["checks_performed"].append("multiple_statements")
        return False, "Múltiplos statements SQL não são permitidos", validation_metadata
    
    validation_metadata["checks_performed"].append("all_passed")
    return True, "", validation_metadata
