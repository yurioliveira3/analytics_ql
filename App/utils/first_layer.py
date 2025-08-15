"""
Módulo para filtros de primeira camada - detecção de saudações, perguntas vagas e respostas diretas.
"""

import re
import random
from utils.logger import get_logger

# Logger para este módulo
logger = get_logger(__name__)


def is_greeting_or_small_talk(text: str) -> bool:
    """
    Detecta se o texto é uma saudação ou conversa casual.
    
    Args:
        text: Texto a ser analisado
        
    Returns:
        True se for saudação ou conversa casual, False caso contrário
    """
    normalized_text = text.lower().strip()
    
    # Padrões de saudações e conversas casuais
    greeting_patterns = [
        # Saudações básicas
        r'^\s*(oi|olá|ola|hey|hi|hello|e aí|eai|salve)\s*[!.]*\s*$',
        r'^\s*(bom dia|boa tarde|boa noite)\s*[!.]*\s*$',
        r'^\s*(tchau|até logo|até mais|bye|goodbye|adeus)\s*[!.]*\s*$',
        
        # Cumprimentos
        r'^\s*(tudo bem|como vai|como está|tudo certo|beleza)\s*[?!.]*\s*$',
        r'^\s*(e então|como você está|tudo ok|tudo joia)\s*[?!.]*\s*$',
        
        # Agradecimentos simples
        r'^\s*(obrigad[oa]|valeu|thanks)\s*[!.]*\s*$',
        r'^\s*(muito obrigad[oa]|)\s*[!.]*\s*$',
        
        # Perguntas sobre o sistema
        r'^\s*(quem é você|o que você faz|você é o que)\s*[?!.]*\s*$',
        r'^\s*(como funciona|para que serve)\s*[?!.]*\s*$',
        
        # Conversas casuais
        r'^\s*(ok|okay|certo|entendi)\s*[!.]*\s*$',
        
        # Teste
        r'^\s*(teste|testing|test)\s*[!.]*\s*$',
    ]
    
    # Verifica se algum padrão de saudação coincide
    for pattern in greeting_patterns:
        if re.search(pattern, normalized_text):
            return True
    
    # Verifica se é muito curto e parece ser saudação (até 20 caracteres)
    if len(normalized_text) <= 20:
        greeting_words = [
            'oi', 'olá', 'ola', 'hey', 'hi', 'hello', 'tchau', 'bye',
            'valeu', 'obrigado', 'obrigada', 'thanks', 'beleza', 'legal',
            'ok', 'okay', 'certo', 'show', 'massa', 'teste', 'test'
        ]
        
        # Se contém apenas palavras de saudação
        words = normalized_text.split()
        if len(words) <= 3 and any(word in greeting_words for word in words):
            return True
    
    return False


def is_vague_question(text: str) -> bool:
    """
    Detecta se a pergunta é muito vaga ou incompleta.
    
    Args:
        text: Texto a ser analisado
        
    Returns:
        True se for muito vaga, False caso contrário
    """
    normalized_text = text.lower().strip()
    
    # Padrões de perguntas muito vagas
    vague_patterns = [
        r'^\s*(me ajuda|ajuda)\s*$',
        r'^\s*(dados|informações?)\s*$',
        r'^\s*(análise|analise|relatório)\s*$',
        r'^\s*(mostre|mostra|exibe|lista)\s*$',
        r'^\s*(quero|preciso|gostaria)\s*$',
        r'^\s*(o que)\s*$',
    ]
    
    # Verifica se algum padrão vago coincide
    for pattern in vague_patterns:
        if re.search(pattern, normalized_text):
            return True
    
    # Se for muito curto e não tem contexto específico
    if len(normalized_text) < 15:
        return True
    
    return False


def log_interaction_type(query: str, interaction_type: str):
    """
    Registra o tipo de interação para métricas de engajamento.
    
    Args:
        query: A pergunta do usuário
        interaction_type: Tipo da interação (greeting, vague, valid_query, etc.)
    """
    logger.info(f"INTERACTION_METRIC | Type: {interaction_type} | Query_Length: {len(query)} | Query: '{query[:50]}{'...' if len(query) > 50 else ''}'")


def get_contextual_suggestions() -> list[str]:
    """
    Retorna uma lista de sugestões de perguntas baseadas em análises de dados genéricas.
    
    Returns:
        Lista de perguntas sugeridas
    """
    suggestions = [
        "Qual a distribuição dos dados por categoria?",
        "Quais são os valores médios por grupo?",
        "Qual período tem maior concentração de registros?",
        "Quais são os top 10 registros por valor?",
        "Como os dados se comportam ao longo do tempo?",
        "Qual a correlação entre as principais variáveis?",
        "Onde estão concentrados os maiores valores?"
    ]
    
    # Retorna 3-4 sugestões aleatórias
    return random.sample(suggestions, min(4, len(suggestions)))


def create_greeting_response() -> tuple[str, str, list[str], str]:
    """
    Cria uma resposta padrão para saudações sem chamar o modelo.
    
    Returns:
        Tuple com resposta formatada como mensagem direta (não executável)
    """
    suggestions = get_contextual_suggestions()
    suggestions_list = "\n".join([f"• {sugg}" for sugg in suggestions[:3]])
    
    # Adiciona um marcador especial para indicar que não é executável
    #[NON_EXECUTABLE_RESPONSE]
    greeting_response = f"""
Sou seu assistente especializado em consultas SQL para análise de dados.

Para começar, experimente uma dessas perguntas:

{suggestions_list}

Ou faça sua própria pergunta específica sobre os dados que gostaria de analisar!"""
    
    explanation = "Saudação recebida - aguardando pergunta específica sobre análise de dados"
    
    return greeting_response, explanation, [], ""


def create_vague_question_response() -> tuple[str, str, list[str], str]:
    """
    Cria uma resposta padrão para perguntas vagas.
    
    Returns:
        Tuple com resposta formatada como mensagem direta (não executável)
    """
    suggestions = get_contextual_suggestions()
    suggestions_list = "\n".join([f"• {sugg}" for sugg in suggestions[:4]])
    
    # Adiciona um marcador especial para indicar que não é executável
    #[NON_EXECUTABLE_RESPONSE]
    vague_response = f"""
Para te ajudar da melhor forma, preciso de uma pergunta mais específica!

Aqui estão algumas sugestões do que você pode perguntar:

{suggestions_list}

Tente ser mais específico sobre:
• Que dados você quer analisar?
• Que tipo de informação está buscando?
• Há algum período ou categoria específica de interesse?"""
    
    explanation = "Pergunta muito vaga - necessário maior especificidade sobre o que analisar"
    
    return vague_response, explanation, [], ""
