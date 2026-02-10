"""
Database module - PostgreSQL with pgvector (v8.2.0)
"""

import json
from datetime import datetime, timezone
from typing import Generator

from pgvector.sqlalchemy import Vector
from sqlalchemy import (JSON, Boolean, Column, DateTime, ForeignKey, Index,
                        Integer, String, Text, create_engine)
from sqlalchemy.orm import (Session, declarative_base, relationship,
                            sessionmaker)

from .config import settings


def _utcnow():
    return datetime.now(timezone.utc)


# Engine SQLAlchemy
engine = create_engine(settings.DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# ===== MODELS =====


class User(Base):
    """Utilisateur"""

    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=True)
    hashed_password = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relations
    conversations = relationship(
        "Conversation", back_populates="user", cascade="all, delete-orphan"
    )
    feedbacks = relationship("Feedback", back_populates="user", cascade="all, delete-orphan")


class Conversation(Base):
    """Conversation"""

    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    title = Column(String(200), default="Nouvelle conversation")
    model = Column(String(100), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    # Relations
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    feedbacks = relationship(
        "Feedback", back_populates="conversation", cascade="all, delete-orphan"
    )


class Message(Base):
    """Message dans une conversation"""

    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(36), ForeignKey("conversations.id"), nullable=False)
    role = Column(String(20), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    model = Column(String(100), nullable=True)
    tools_used = Column(JSON, nullable=True)  # jsonb list
    thinking = Column(JSON, nullable=True)  # jsonb object
    created_at = Column(DateTime(timezone=True), default=_utcnow)

    # Relations
    conversation = relationship("Conversation", back_populates="messages")
    feedbacks = relationship("Feedback", back_populates="message", cascade="all, delete-orphan")


class Tool(Base):
    """Outil disponible"""

    __tablename__ = "tools"

    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    category = Column(String(50), default="general")
    enabled = Column(Boolean, default=True)
    usage_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=_utcnow)


class Feedback(Base):
    """Feedback utilisateur sur les reponses"""

    __tablename__ = "feedbacks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(
        Integer, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True
    )
    conversation_id = Column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    feedback_type = Column(String(20), nullable=False)  # positive, negative, correction
    context = Column(
        JSON, nullable=True
    )  # jsonb: query, response, corrected_response, tools_used, reason

    created_at = Column(DateTime(timezone=True), default=_utcnow, index=True)

    # Relations
    message = relationship("Message", back_populates="feedbacks")
    conversation = relationship("Conversation", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")


class AuditLog(Base):
    """Log d'audit pour tracabilite des actions sensibles"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=_utcnow, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)

    # Action
    action = Column(String(100), nullable=False, index=True)
    resource = Column(String(200), nullable=True)

    # Resultat
    allowed = Column(Boolean, nullable=False, default=True)
    role = Column(String(50), nullable=True)

    # Details (JSONB in PostgreSQL): command, parameters, result merged
    details = Column(JSON, nullable=True)  # jsonb

    # Contexte
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(255), nullable=True)


class LearningMemory(Base):
    """Memoire d'apprentissage (remplace ChromaDB)"""

    __tablename__ = "learning_memories"

    id = Column(String(36), primary_key=True)
    collection = Column(String(50), nullable=False, index=True)
    content = Column(Text, nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)  # jsonb - renamed to avoid conflict
    embedding = Column(Vector(1024), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_utcnow)
    updated_at = Column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ===== DATABASE INDEXES (Performance) =====

Index("ix_message_conversation_created", Message.conversation_id, Message.created_at)
Index("ix_conversation_user_updated", Conversation.user_id, Conversation.updated_at)
Index("ix_audit_user_timestamp", AuditLog.user_id, AuditLog.timestamp)


# ===== DATABASE FUNCTIONS =====


def init_db():
    """Initialiser la base de donnees"""
    Base.metadata.create_all(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependency pour obtenir une session DB"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session() -> Session:
    """Obtenir une session directe (pour usage hors FastAPI)"""
    return SessionLocal()
