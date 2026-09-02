from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_payload
from backend.app.schemas.chat import (
    ChatQueryRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatMessageResponse
)
from backend.app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat & RAG Assistant"])

@router.post("", response_model=ChatResponse)
def ask_question(
    request: ChatQueryRequest,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Ask a question to the permission-aware Banking Knowledge Assistant.
    Executes input guardrails, vector retrieval filtered by user role, Groq generation, and output guardrails.
    """
    user_id = int(payload.get("sub"))
    user_roles = payload.get("roles", [])
    return ChatService.process_query(
        db=db,
        user_id=user_id,
        user_roles=user_roles,
        request=request
    )

@router.get("/sessions", response_model=List[ChatSessionResponse])
def get_sessions(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    List all chat sessions for the authenticated user.
    """
    user_id = int(payload.get("sub"))
    return ChatService.get_user_sessions(db, user_id)

@router.get("/history/{session_id}", response_model=List[ChatMessageResponse])
def get_session_history(
    session_id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Fetch chronological message history and structured citations for a given session.
    """
    user_id = int(payload.get("sub"))
    return ChatService.get_session_history(db, session_id, user_id)

@router.delete("/sessions/{session_id}")
def delete_session(
    session_id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Delete a chat session and all associated messages.
    """
    user_id = int(payload.get("sub"))
    ChatService.delete_session(db, session_id, user_id)
    return {"success": True, "message": "Chat session deleted successfully"}
