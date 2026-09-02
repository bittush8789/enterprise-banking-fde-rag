import json
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models import ChatSession, ChatMessage, User
from backend.app.schemas.chat import (
    ChatQueryRequest,
    ChatResponse,
    ChatSessionResponse,
    ChatMessageResponse,
    SourceCitation
)
from backend.app.guardrails.input_guardrail import InputGuardrail
from backend.app.rag.rag_chain import RAGChain
from backend.app.services.audit_service import AuditService

logger = logging.getLogger("bankassist.chat_service")

class ChatService:
    @staticmethod
    def create_session(db: Session, user_id: int, title: str = "New Conversation") -> ChatSession:
        session = ChatSession(user_id=user_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session

    @staticmethod
    def get_user_sessions(db: Session, user_id: int) -> List[ChatSessionResponse]:
        sessions = (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.updated_at.desc())
            .all()
        )
        results = []
        for s in sessions:
            results.append(ChatSessionResponse(
                id=s.id,
                user_id=s.user_id,
                title=s.title,
                created_at=s.created_at,
                updated_at=s.updated_at,
                message_count=len(s.messages)
            ))
        return results

    @staticmethod
    def get_session_history(db: Session, session_id: int, user_id: int) -> List[ChatMessageResponse]:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access to this chat session is forbidden")

        messages = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

        response_list = []
        for m in messages:
            sources_data = []
            if m.sources:
                try:
                    raw_sources = json.loads(m.sources)
                    sources_data = [SourceCitation(**item) for item in raw_sources]
                except Exception:
                    sources_data = []

            response_list.append(ChatMessageResponse(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                sources=sources_data,
                created_at=m.created_at
            ))
        return response_list

    @staticmethod
    def delete_session(db: Session, session_id: int, user_id: int) -> bool:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        if session.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        db.delete(session)
        db.commit()
        return True

    @staticmethod
    def process_query(
        db: Session,
        user_id: int,
        user_roles: List[str],
        request: ChatQueryRequest,
    ) -> ChatResponse:
        # 1. Resolve or Create Chat Session
        session = None
        if request.session_id:
            session = db.query(ChatSession).filter(ChatSession.id == request.session_id).first()
            if not session or session.user_id != user_id:
                session = None

        if not session:
            # Generate a title from the first 4-5 words of the query
            preview_title = " ".join(request.query.strip().split()[:5])
            if len(preview_title) > 30:
                preview_title = preview_title[:30] + "..."
            session = ChatService.create_session(db, user_id, title=preview_title or "Banking Chat")

        raw_query = request.query.strip()

        # 2. Input Guardrails (Prompt Injection + PII Detection)
        guardrail_result = InputGuardrail.validate_and_sanitize(raw_query)

        # Handle Blocked Prompt Injections
        if not guardrail_result["is_safe"]:
            AuditService.log_event(
                db=db,
                event_type="PROMPT_INJECTION_DETECTED",
                event_status="BLOCKED",
                user_id=user_id,
                details={
                    "query": raw_query,
                    "reasons": guardrail_result["details"]
                }
            )

            # Record in session messages
            user_msg = ChatMessage(session_id=session.id, role="user", content=raw_query)
            db.add(user_msg)
            db.flush()

            refusal_text = guardrail_result["response_message"]
            bot_msg = ChatMessage(
                session_id=session.id,
                role="assistant",
                content=refusal_text,
                sources=None
            )
            db.add(bot_msg)
            db.commit()

            return ChatResponse(
                session_id=session.id,
                user_message_id=user_msg.id,
                assistant_message_id=bot_msg.id,
                query=raw_query,
                answer=refusal_text,
                sources=[],
                is_blocked=True,
                security_event="PROMPT_INJECTION_DETECTED"
            )

        # Handle PII Detected in Input
        if guardrail_result["pii_detected"]:
            AuditService.log_event(
                db=db,
                event_type="PII_DETECTED",
                event_status="WARNING",
                user_id=user_id,
                details={"entities": [e["entity_type"] for e in guardrail_result["pii_entities"]]}
            )
            AuditService.log_event(
                db=db,
                event_type="PII_MASKED",
                event_status="SUCCESS",
                user_id=user_id,
                details={"masked_query": guardrail_result["sanitized_query"]}
            )

        sanitized_query = guardrail_result["sanitized_query"]

        # 3. Permission-Aware RAG Pipeline Execution
        rag_output = RAGChain.execute(
            query=sanitized_query,
            user_roles=user_roles
        )

        answer_text = rag_output["answer"]
        sources: List[SourceCitation] = rag_output["sources"]
        event_name = rag_output.get("event", "CHAT_QUERY")

        # 4. Audit Logging for RAG Event
        AuditService.log_event(
            db=db,
            event_type=event_name,
            event_status="SUCCESS" if rag_output["is_grounded"] else "WARNING",
            user_id=user_id,
            details={
                "query": sanitized_query,
                "sources_count": len(sources),
                "roles": user_roles
            }
        )

        # 5. Persist Chat Messages
        user_msg = ChatMessage(
            session_id=session.id,
            role="user",
            content=sanitized_query
        )
        db.add(user_msg)
        db.flush()

        sources_json = json.dumps([s.model_dump() for s in sources]) if sources else None
        bot_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=answer_text,
            sources=sources_json
        )
        db.add(bot_msg)
        db.commit()

        return ChatResponse(
            session_id=session.id,
            user_message_id=user_msg.id,
            assistant_message_id=bot_msg.id,
            query=sanitized_query,
            answer=answer_text,
            sources=sources,
            is_blocked=False,
            security_event=event_name if event_name != "CHAT_QUERY" else None
        )
