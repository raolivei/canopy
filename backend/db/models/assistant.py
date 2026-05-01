"""Database models for AI Assistant."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.base import Base


class AssistantConversation(Base):
    """Conversation thread."""
    
    __tablename__ = "assistant_conversations"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    
    messages: Mapped[list["AssistantMessage"]] = relationship(
        "AssistantMessage", back_populates="conversation", cascade="all, delete-orphan"
    )


class AssistantMessage(Base):
    """Message in conversation."""
    
    __tablename__ = "assistant_messages"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assistant_conversations.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(String(20))  # 'user' or 'assistant'
    content: Mapped[str] = mapped_column(Text)
    functions_called: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    conversation: Mapped["AssistantConversation"] = relationship("AssistantConversation", back_populates="messages")
