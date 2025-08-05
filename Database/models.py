"""
Modelos SQLAlchemy para persistência do histórico de chats.
"""

from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, BigInteger, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid

Base = declarative_base()


class chat_sessions(Base):
    """Sessões de chat - uma linha por conversa/aba."""
    
    __tablename__ = "chat_sessions"
    __table_args__ = {"schema": "metadata"}
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=True)  # Futuro: integração com sistema de usuários
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    title = Column(Text, nullable=True)  # Título da conversa
    deleted = Column(Boolean, nullable=False, default=False)  # Soft delete
    
    # Relacionamento com mensagens
    messages = relationship("chat_messages", back_populates="session", cascade="all, delete-orphan")


class chat_messages(Base):
    """Mensagens do chat - perguntas e respostas."""
    
    __tablename__ = "chat_messages"
    __table_args__ = {"schema": "metadata"}
    
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(UUID(as_uuid=True), ForeignKey("metadata.chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(10), nullable=False)  # 'user' ou 'assistant'
    content = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    deleted = Column(Boolean, nullable=False, default=False)  # Soft delete
    
    # Campos específicos para mensagens do assistente
    generated_query = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    used_tables = Column(Text, nullable=True)  # JSON string
    ml_algorithm = Column(String(100), nullable=True)
    execution_result = Column(Text, nullable=True)  # JSON string dos resultados
    execution_time_ms = Column(Integer, nullable=True)
    total_cost = Column(String(50), nullable=True)
    plan_rows = Column(Integer, nullable=True)
    chart_type = Column(String(50), nullable=True)
    insights = Column(Text, nullable=True)
    
    # Relacionamento com sessão
    session = relationship("chat_sessions", back_populates="messages")


# Manter compatibilidade com a tabela existente chat_history
class chat_history(Base):
    """Tabela legada - manter para migração gradual."""
    
    __tablename__ = "chat_history"
    __table_args__ = {"schema": "metadata"}
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(128), nullable=False)
    user_question = Column(Text, nullable=False)
    generated_query = Column(Text, nullable=True)
    execution_result = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=True)
