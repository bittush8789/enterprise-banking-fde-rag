from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel

class SourceCitation(BaseModel):
    document_id: Optional[str] = None
    document_name: str
    page_number: Optional[int] = 1
    section: Optional[str] = None
    score: Optional[float] = None
    excerpt: Optional[str] = None

class ChatQueryRequest(BaseModel):
    session_id: Optional[int] = None
    query: str

class ChatResponse(BaseModel):
    session_id: int
    user_message_id: int
    assistant_message_id: int
    query: str
    answer: str
    sources: List[SourceCitation] = []
    is_blocked: bool = False
    security_event: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[List[SourceCitation]] = []
    created_at: datetime

    class Config:
        from_attributes = True

class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0

    class Config:
        from_attributes = True
