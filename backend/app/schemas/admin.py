from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
from backend.app.schemas.auth import UserResponse

class UserRoleUpdateRequest(BaseModel):
    roles: List[str]

class UserStatusUpdateRequest(BaseModel):
    is_active: bool

class AuditLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_email: Optional[str] = None
    event_type: str
    event_status: str
    details: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True

class SecurityStatsResponse(BaseModel):
    total_blocked_requests: int
    prompt_injection_attempts: int
    pii_detection_events: int
    unauthorized_access_attempts: int
    low_score_fallbacks: int
    total_queries: int
    total_documents: int
    total_users: int
