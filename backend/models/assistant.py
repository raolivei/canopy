"""Pydantic models for AI Assistant API."""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    
    query: str = Field(..., min_length=1, max_length=1000, description="User's question")
    conversation_id: Optional[int] = Field(None, description="Conversation ID for follow-up questions")


class FunctionCall(BaseModel):
    """Function call made by the assistant."""
    
    name: str
    arguments: dict[str, Any]
    result: Any


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    
    response: str
    conversation_id: int
    message_id: int
    functions_called: list[FunctionCall]
    execution_time_ms: int


class Message(BaseModel):
    """A single message in conversation history."""
    
    id: int
    role: str  # 'user' or 'assistant'
    content: str
    functions_called: Optional[list[FunctionCall]] = None
    created_at: datetime


class Conversation(BaseModel):
    """Conversation with message history."""
    
    id: int
    created_at: datetime
    updated_at: datetime
    messages: list[Message]
