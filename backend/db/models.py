import uuid
from datetime import datetime
from typing import Optional, List, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    func
)
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from backend.db.database import Base
from backend.core.config import get_settings

settings = get_settings()


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type if available, otherwise CHAR(36), storing as string.
    """
    impl = CHAR(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == "postgresql":
            if isinstance(value, uuid.UUID):
                return value
            return uuid.UUID(str(value))
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(uuid.UUID(str(value)))

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class VectorType(TypeDecorator):
    """Platform-independent Vector type.
    Uses pgvector Vector on PostgreSQL, otherwise JSON on SQLite/other dialects.
    """
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            try:
                from pgvector.sqlalchemy import Vector
                return dialect.type_descriptor(Vector(settings.EMBEDDING_DIMENSION))
            except Exception:
                return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if isinstance(value, list):
            return value
        return list(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return value


class Conversation(Base):
    """
    Represents an ongoing chat session or conversation thread.
    """
    __tablename__ = "conversations"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), default="New Conversation", nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at"
    )
    documents = relationship(
        "Document",
        back_populates="conversation"
    )


class Message(Base):
    """
    Represents an individual message exchanged in a conversation.
    Supports multimodal inputs and responses.
    """
    __tablename__ = "messages"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        GUID(),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(String(32), nullable=False)  # "user", "assistant", "system"
    content = Column(Text, nullable=False)
    modality = Column(String(32), default="text", nullable=False)  # "text", "image", "audio", "document"
    extra_metadata = Column(JSON, nullable=True)  # Sources, citations, audio URLs, timings
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class Document(Base):
    """
    Represents an uploaded document (PDF, TXT, DOCX, or generated file).
    Maintains document versions and points to storage path.
    """
    __tablename__ = "documents"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        GUID(),
        ForeignKey("conversations.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    filename = Column(String(255), nullable=False)
    file_type = Column(String(32), nullable=False)  # "pdf", "docx", "txt", "image"
    file_path = Column(String(512), nullable=True)
    extracted_text = Column(Text, nullable=True)
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="documents")
    chunks = relationship(
        "DocumentChunk",
        back_populates="document",
        cascade="all, delete-orphan",
        order_by="DocumentChunk.chunk_index"
    )


class DocumentChunk(Base):
    """
    Represents a contextual text chunk derived from an uploaded document.
    Stores dense vector embedding for RAG similarity search via pgvector or cosine similarity.
    """
    __tablename__ = "document_chunks"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    document_id = Column(
        GUID(),
        ForeignKey("documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding = Column(VectorType(), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    document = relationship("Document", back_populates="chunks")
