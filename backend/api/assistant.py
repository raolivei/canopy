"""AI Assistant API endpoints."""

from typing import Optional

from fastapi import APIRouter, HTTPException
from sqlalchemy import desc, select

from backend.app.config import get_settings
from backend.db.models.assistant import AssistantConversation, AssistantMessage
from backend.db.session import DbSession
from backend.models.assistant import ChatRequest, ChatResponse, Conversation, FunctionCall, Message
from backend.models.golden_questions import GoldenQuestionsRunRequest, GoldenQuestionsRunResponse
from backend.services.assistant_service import AssistantService
from backend.services.golden_questions import GoldenQuestionsService

router = APIRouter(prefix="/v1/assistant", tags=["assistant"])


def _get_assistant_service(db: DbSession) -> AssistantService:
    """Create assistant service with config from settings."""
    settings = get_settings()
    
    return AssistantService(
        db=db,
        provider_type=settings.assistant_provider,
        openclaw_url=settings.openclaw_url,
        openclaw_model=settings.openclaw_model,
        ollama_host=settings.ollama_host,
        ollama_model=settings.ollama_model,
    )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: DbSession):
    """Send a chat message to the assistant."""
    try:
        # Get or create conversation
        if request.conversation_id:
            conversation = db.get(AssistantConversation, request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
        else:
            conversation = AssistantConversation()
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # Get conversation history
        history_query = select(AssistantMessage).where(
            AssistantMessage.conversation_id == conversation.id
        ).order_by(AssistantMessage.created_at)
        
        messages = db.execute(history_query).scalars().all()
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        # Get assistant service and process query
        assistant = _get_assistant_service(db)
        result = assistant.chat(request.query, history)
        
        # Save user message
        user_msg = AssistantMessage(
            conversation_id=conversation.id,
            role="user",
            content=request.query
        )
        db.add(user_msg)
        
        # Save assistant response
        assistant_msg = AssistantMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=result["response"],
            functions_called=result.get("functions_called"),
            execution_time_ms=result.get("execution_time_ms")
        )
        db.add(assistant_msg)
        db.commit()
        db.refresh(assistant_msg)
        
        # Build response
        return ChatResponse(
            response=result["response"],
            conversation_id=conversation.id,
            message_id=assistant_msg.id,
            functions_called=[
                FunctionCall(**fc) for fc in result.get("functions_called", [])
            ],
            execution_time_ms=result.get("execution_time_ms", 0)
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assistant error: {str(e)}")


@router.get("/conversations", response_model=list[Conversation])
async def get_conversations(db: DbSession, limit: int = 10):
    """Get recent conversations."""
    query = select(AssistantConversation).order_by(
        desc(AssistantConversation.updated_at)
    ).limit(limit)
    
    conversations = db.execute(query).scalars().all()
    
    return [
        Conversation(
            id=conv.id,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            messages=[
                Message(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    functions_called=[
                        FunctionCall(**fc) for fc in (msg.functions_called or [])
                    ] if msg.functions_called else None,
                    created_at=msg.created_at
                )
                for msg in conv.messages
            ]
        )
        for conv in conversations
    ]


@router.get("/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: int, db: DbSession):
    """Get a specific conversation with history."""
    conversation = db.get(AssistantConversation, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return Conversation(
        id=conversation.id,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[
            Message(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                functions_called=[
                    FunctionCall(**fc) for fc in (msg.functions_called or [])
                ] if msg.functions_called else None,
                created_at=msg.created_at
            )
            for msg in conversation.messages
        ]
    )


@router.post("/golden-questions/run", response_model=GoldenQuestionsRunResponse)
async def run_golden_questions(
    request: GoldenQuestionsRunRequest,
    db: DbSession
):
    """Execute golden questions regression suite comparing Canopy vs Monarch MCP."""
    try:
        service = GoldenQuestionsService(db)
        result = service.run_golden_questions(
            verbose=request.verbose,
            stop_on_failure=request.stop_on_failure
        )
        return GoldenQuestionsRunResponse(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Golden questions error: {str(e)}")
