"""
Serviços para gerenciamento do histórico de chats.
"""
from Database.models import chat_sessions, chat_messages, chat_history
from Database.database import get_db
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from datetime import datetime
import json
import uuid

class chat_service:
    """Serviço para gerenciamento de sessões e mensagens de chat."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_session(self, title: Optional[str] = None) -> str:
        """Cria uma nova sessão de chat.
        
        Args:
            title: Título opcional da sessão.
            
        Returns:
            ID da sessão criada.
        """
        session = chat_sessions(
            title=title or f"Chat {datetime.now().strftime('%d/%m/%Y %H:%M')}"
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return str(session.id)
    
    def save_user_message(self, session_id: str, content: str) -> int:
        """Salva uma mensagem do usuário.
        
        Args:
            session_id: ID da sessão.
            content: Conteúdo da mensagem.
            
        Returns:
            ID da mensagem criada.
        """
        message = chat_messages(
            session_id=uuid.UUID(session_id),
            role="user",
            content=content,
            token_count=len(content.split())  # Estimativa simples
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message.id
    
    def save_assistant_message(
        self, 
        session_id: str, 
        content: str,
        generated_query: Optional[str] = None,
        explanation: Optional[str] = None,
        used_tables: Optional[List[str]] = None,
        ml_algorithm: Optional[str] = None,
        execution_result: Optional[Dict] = None,
        execution_time_ms: Optional[int] = None,
        total_cost: Optional[str] = None,
        plan_rows: Optional[int] = None,
        chart_type: Optional[str] = None,
        insights: Optional[str] = None
    ) -> int:
        """Salva uma mensagem do assistente com metadados.
        
        Args:
            session_id: ID da sessão.
            content: Conteúdo da resposta.
            generated_query: Query SQL gerada.
            explanation: Explicação da query.
            used_tables: Lista de tabelas utilizadas.
            ml_algorithm: Algoritmo de ML aplicado.
            execution_result: Resultado da execução.
            execution_time_ms: Tempo de execução em ms.
            total_cost: Custo total da operação.
            plan_rows: Número de linhas do plano.
            chart_type: Tipo de gráfico sugerido.
            insights: Insights gerados.
            
        Returns:
            ID da mensagem criada.
        """
        message = chat_messages(
            session_id=uuid.UUID(session_id),
            role="assistant",
            content=content,
            token_count=len(content.split()),
            generated_query=generated_query,
            explanation=explanation,
            used_tables=json.dumps(used_tables) if used_tables else None,
            ml_algorithm=ml_algorithm,
            execution_result=json.dumps(execution_result, default=str) if execution_result else None,
            execution_time_ms=execution_time_ms,
            total_cost=total_cost,
            plan_rows=plan_rows,
            chart_type=chart_type,
            insights=insights
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message.id
    
    def get_session_history(self, session_id: str, limit: int = 50) -> List[Dict]:
        """Recupera o histórico de uma sessão não deletada.
        
        Args:
            session_id: ID da sessão.
            limit: Número máximo de mensagens.
            
        Returns:
            Lista de mensagens da sessão.
        """
        messages = (
            self.db.query(chat_messages)
            .filter(and_(
                chat_messages.session_id == uuid.UUID(session_id),
                chat_messages.deleted == False
            ))
            .order_by(desc(chat_messages.created_at))
            .limit(limit)
            .all()
        )
        
        return [self._message_to_dict(msg) for msg in reversed(messages)]
    
    def get_sessions_list(self, limit: int = 20) -> List[Dict]:
        """Lista as sessões não deletadas ordenadas por data de criação (mais novo primeiro).
        
        Args:
            limit: Número máximo de sessões.
            
        Returns:
            Lista de sessões com última mensagem.
        """
        sessions = (
            self.db.query(chat_sessions)
            .filter(chat_sessions.deleted == False)
            .order_by(desc(chat_sessions.created_at))
            .limit(limit)
            .all()
        )
        
        result = []
        for session in sessions:
            # Busca a última mensagem não deletada da sessão
            last_message = (
                self.db.query(chat_messages)
                .filter(and_(
                    chat_messages.session_id == session.id,
                    chat_messages.deleted == False
                ))
                .order_by(desc(chat_messages.created_at))
                .first()
            )
            
            result.append({
                "id": str(session.id),
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "last_message": last_message.content[:100] + "..." if last_message and len(last_message.content) > 100 else (last_message.content if last_message else ""),
                "last_activity": last_message.created_at.isoformat() if last_message else session.created_at.isoformat()
            })
        
        return result
    
    def update_session_title(self, session_id: str, title: str) -> bool:
        """Atualiza o título de uma sessão não deletada.
        
        Args:
            session_id: ID da sessão.
            title: Novo título.
            
        Returns:
            True se atualizado com sucesso.
        """
        session = (
            self.db.query(chat_sessions)
            .filter(and_(
                chat_sessions.id == uuid.UUID(session_id),
                chat_sessions.deleted == False
            ))
            .first()
        )
        
        if session:
            session.title = title
            self.db.commit()
            return True
        return False
    
    def delete_session(self, session_id: str) -> bool:
        """Marca uma sessão como deletada (soft delete).
        
        Args:
            session_id: ID da sessão.
            
        Returns:
            True se marcado como deletado com sucesso.
        """
        session = (
            self.db.query(chat_sessions)
            .filter(and_(
                chat_sessions.id == uuid.UUID(session_id),
                chat_sessions.deleted == False
            ))
            .first()
        )
        
        if session:
            session.deleted = True
            # Marca todas as mensagens da sessão como deletadas também
            self.db.query(chat_messages).filter(
                chat_messages.session_id == uuid.UUID(session_id)
            ).update({"deleted": True})
            self.db.commit()
            return True
        return False
    
    def restore_session(self, session_id: str) -> bool:
        """Restaura uma sessão deletada (desfaz soft delete).
        
        Args:
            session_id: ID da sessão.
            
        Returns:
            True se restaurado com sucesso.
        """
        session = (
            self.db.query(chat_sessions)
            .filter(and_(
                chat_sessions.id == uuid.UUID(session_id),
                chat_sessions.deleted == True
            ))
            .first()
        )
        
        if session:
            session.deleted = False
            # Restaura todas as mensagens da sessão também
            self.db.query(chat_messages).filter(
                chat_messages.session_id == uuid.UUID(session_id)
            ).update({"deleted": False})
            self.db.commit()
            return True
        return False
    
    def migrate_legacy_history(self) -> int:
        """Migra dados da tabela chat_history para o novo formato.
        
        Returns:
            Número de registros migrados.
        """
        legacy_records = self.db.query(chat_history).all()
        migrated_count = 0
        
        # Agrupa por session_id para criar sessões
        sessions_map = {}
        
        for record in legacy_records:
            session_id_str = record.session_id
            
            # Cria sessão se não existe
            if session_id_str not in sessions_map:
                new_session = chat_sessions(
                    title=f"Chat Migrado {record.created_at.strftime('%d/%m/%Y %H:%M')}",
                    created_at=record.created_at
                )
                self.db.add(new_session)
                self.db.flush()  # Para obter o ID
                sessions_map[session_id_str] = new_session.id
            
            # Cria mensagem do usuário
            user_message = chat_messages(
                session_id=sessions_map[session_id_str],
                role="user",
                content=record.user_question,
                created_at=record.created_at
            )
            self.db.add(user_message)
            
            # Cria mensagem do assistente se houver query
            if record.generated_query:
                assistant_message = chat_messages(
                    session_id=sessions_map[session_id_str],
                    role="assistant",
                    content=f"Query gerada: {record.generated_query}",
                    generated_query=record.generated_query,
                    execution_result=record.execution_result,
                    created_at=record.created_at
                )
                self.db.add(assistant_message)
            
            migrated_count += 1
        
        self.db.commit()
        return migrated_count
    
    def _message_to_dict(self, message: chat_messages) -> Dict:
        """Converte uma mensagem para dicionário."""
        result = {
            "id": message.id,
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "token_count": message.token_count
        }
        
        # Adiciona campos específicos do assistente se existirem
        if message.role == "assistant":
            result.update({
                "generated_query": message.generated_query,
                "explanation": message.explanation,
                "used_tables": json.loads(message.used_tables) if message.used_tables else None,
                "ml_algorithm": message.ml_algorithm,
                "execution_result": json.loads(message.execution_result) if message.execution_result else None,
                "execution_time_ms": message.execution_time_ms,
                "total_cost": message.total_cost,
                "plan_rows": message.plan_rows,
                "chart_type": message.chart_type,
                "insights": message.insights
            })
        
        return result


def get_chat_service(db: Session = None) -> chat_service:
    """Factory function para obter instância do serviço de chat."""
    if db is None:
        db = next(get_db())
    return chat_service(db)
