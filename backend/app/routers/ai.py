from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.chat_message import ChatMessage
from app.dependencies.auth import get_current_user
from app.schemas.ai import ChatRequest, ChatResponse
from app.services import ai_service

router = APIRouter(prefix="/ai", tags=["AI Chatbot"])


@router.post("/chat", response_model=ChatResponse)
def chat_with_bot(
    chat_in: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Chat with the AI assistant in English, Hindi, or Hinglish.
    Automatically parses intents, extracts amounts, and records transactions/savings directly in the database.
    """
    return ai_service.process_chat_message(db, current_user.id, chat_in.message)


@router.get("/history")
def get_chat_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Retrieve user's chat message history."""
    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(50)
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "message": m.message,
            "created_at": m.created_at.isoformat(),
        }
        for m in messages
    ]
