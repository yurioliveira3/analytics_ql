"""
Configura# Configuração da conexão com o banco
DATABASE_URL = os.getenv(
    "PG_CONNECTION_STRING", 
    "postgresql://localhost:5432/analytics_db"
)o banco de dados e sessões.
"""

from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine
from typing import Generator
from .models import Base
import os

# Configuração da conexão com o banco
DATABASE_URL = os.getenv(
    "PG_CONNECTION_STRING", 
    "postgresql://localhost:5432/analytics_db"
)

# Engine síncrono para compatibilidade com código existente
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,
    echo=False  # True para debug SQL
)

# Engine assíncrono para operações futuras
# async_engine = create_async_engine(
#     DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
#     pool_size=10,
#     max_overflow=20,
#     pool_recycle=3600,
#     echo=False
# )

# Session makers
SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine
)

# AsyncSessionLocal = async_sessionmaker(
#     async_engine, 
#     expire_on_commit=False
# )


def get_db() -> Generator[Session, None, None]:
    """Dependency injection para sessões síncronas."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# async def get_async_db():
#     """Dependency injection para sessões assíncronas."""
#     async with AsyncSessionLocal() as session:
#         yield session


def create_tables():
    """Cria as tabelas no banco de dados."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Remove todas as tabelas (cuidado!)."""
    Base.metadata.drop_all(bind=engine)
