"""Data models — AI scaffold: User (auth) + the AI module entities.

Domain entity models are STAMPED below the marker by Aakaar's type stamper from the build
contract. Embeddings are stored as JSON text (portable across SQLite/Postgres); swap to
pgvector's Vector type only when scaling retrieval (see ai/vector_store.py).
"""
import uuid

from sqlalchemy import Column, ForeignKey, Integer, String, TIMESTAMP, Text, func

from database.config import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=_uuid)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    filename = Column(String, nullable=False)
    status = Column(String, nullable=False, default="processing")   # processing|ready|failed
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String, primary_key=True, default=_uuid)
    document_id = Column(String, ForeignKey("documents.id"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Text, nullable=False)          # JSON-encoded vector
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(String, primary_key=True, default=_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    title = Column(String, nullable=False, default="New chat")
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(String, primary_key=True, default=_uuid)
    session_id = Column(String, ForeignKey("chat_sessions.id"), nullable=False, index=True)
    role = Column(String, nullable=False)             # user|assistant
    content = Column(Text, nullable=False)
    meta_data = Column("metadata", Text, nullable=True)   # JSON (citations etc.)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)


# ── AAKAAR:STAMPED_MODELS (do not remove this marker) ─────────────────────────────
