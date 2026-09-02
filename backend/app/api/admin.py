from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.app.core.database import get_db
from backend.app.core.security import require_roles
from backend.app.models import User, Role, Document, AuditLog, ChatMessage
from backend.app.schemas.auth import UserResponse
from backend.app.schemas.admin import (
    UserRoleUpdateRequest,
    UserStatusUpdateRequest,
    AuditLogResponse,
    SecurityStatsResponse
)
from backend.app.services.audit_service import AuditService

router = APIRouter(prefix="/admin", tags=["Admin & Security Operations"])

@router.get("/users", response_model=List[UserResponse])
def list_users(
    payload: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    List all banking users and their roles (Admin only).
    """
    users = db.query(User).order_by(User.id.asc()).all()
    return [UserResponse.from_orm(u) for u in users]

@router.put("/users/{user_id}/role", response_model=UserResponse)
def update_user_role(
    user_id: int,
    req: UserRoleUpdateRequest,
    payload: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Assign roles to a user account (Admin only).
    """
    admin_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    # Clear and assign new roles
    user.roles.clear()
    for rname in req.roles:
        role = db.query(Role).filter(Role.name == rname.upper()).first()
        if not role:
            role = Role(name=rname.upper(), description=f"Banking {rname} Role")
            db.add(role)
            db.flush()
        user.roles.append(role)

    db.commit()
    db.refresh(user)

    AuditService.log_event(
        db=db,
        event_type="USER_ROLE_UPDATED",
        event_status="SUCCESS",
        user_id=admin_id,
        details={"target_user_id": user.id, "target_email": user.email, "new_roles": req.roles}
    )

    return UserResponse.from_orm(user)

@router.put("/users/{user_id}/status", response_model=UserResponse)
def update_user_status(
    user_id: int,
    req: UserStatusUpdateRequest,
    payload: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Activate or deactivate a user account (Admin only).
    """
    admin_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = req.is_active
    db.commit()
    db.refresh(user)

    AuditService.log_event(
        db=db,
        event_type="USER_STATUS_UPDATED",
        event_status="SUCCESS",
        user_id=admin_id,
        details={"target_user_id": user.id, "is_active": user.is_active}
    )

    return UserResponse.from_orm(user)

@router.get("/audit-logs", response_model=List[AuditLogResponse])
def get_audit_logs(
    event_type: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    payload: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Retrieve security and operational audit logs (Admin only).
    """
    query = db.query(AuditLog)
    if event_type:
        query = query.filter(AuditLog.event_type == event_type)

    logs = query.order_by(AuditLog.created_at.desc()).limit(limit).all()

    response_list = []
    for log in logs:
        user_email = log.user.email if log.user else "System/Anonymous"
        response_list.append(AuditLogResponse(
            id=log.id,
            user_id=log.user_id,
            user_email=user_email,
            event_type=log.event_type,
            event_status=log.event_status,
            details=log.details,
            created_at=log.created_at
        ))
    return response_list

@router.get("/security-events", response_model=SecurityStatsResponse)
def get_security_stats(
    payload: dict = Depends(require_roles(["ADMIN"])),
    db: Session = Depends(get_db)
):
    """
    Aggregate security event metrics and system counts (Admin only).
    """
    total_blocked = db.query(AuditLog).filter(AuditLog.event_status == "BLOCKED").count()
    prompt_injections = db.query(AuditLog).filter(AuditLog.event_type == "PROMPT_INJECTION_DETECTED").count()
    pii_events = db.query(AuditLog).filter(AuditLog.event_type.in_(["PII_DETECTED", "PII_MASKED", "PII_MASKED_IN_OUTPUT"])).count()
    unauthorized = db.query(AuditLog).filter(AuditLog.event_type == "UNAUTHORIZED_ACCESS").count()
    low_score = db.query(AuditLog).filter(AuditLog.event_type == "LOW_RETRIEVAL_SCORE").count()
    
    total_queries = db.query(ChatMessage).filter(ChatMessage.role == "user").count()
    total_documents = db.query(Document).count()
    total_users = db.query(User).count()

    return SecurityStatsResponse(
        total_blocked_requests=total_blocked,
        prompt_injection_attempts=prompt_injections,
        pii_detection_events=pii_events,
        unauthorized_access_attempts=unauthorized,
        low_score_fallbacks=low_score,
        total_queries=total_queries,
        total_documents=total_documents,
        total_users=total_users
    )
