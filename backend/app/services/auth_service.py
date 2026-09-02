from typing import List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from backend.app.models import User, Role
from backend.app.schemas.auth import UserRegister, UserLogin, Token, UserResponse, RoleResponse
from backend.app.core.security import verify_password, get_password_hash, create_access_token
from backend.app.services.audit_service import AuditService

class AuthService:
    @staticmethod
    def register_user(db: Session, user_in: UserRegister) -> UserResponse:
        existing = db.query(User).filter(User.email == user_in.email.lower()).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )

        # Hash password securely
        hashed_password = get_password_hash(user_in.password)

        new_user = User(
            name=user_in.name,
            email=user_in.email.lower(),
            password_hash=hashed_password,
            is_active=True,
        )

        # Assign requested roles
        roles_to_assign = user_in.roles or ["CUSTOMER_SUPPORT"]
        for role_name in roles_to_assign:
            role = db.query(Role).filter(Role.name == role_name.upper()).first()
            if not role:
                role = Role(name=role_name.upper(), description=f"Banking {role_name} Role")
                db.add(role)
                db.flush()
            new_user.roles.append(role)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        AuditService.log_event(
            db=db,
            event_type="USER_REGISTERED",
            event_status="SUCCESS",
            user_id=new_user.id,
            details={"email": new_user.email, "roles": [r.name for r in new_user.roles]}
        )

        return UserResponse.from_orm(new_user)

    @staticmethod
    def authenticate_user(db: Session, login_data: UserLogin) -> Token:
        user = db.query(User).filter(User.email == login_data.email.lower()).first()
        if not user or not verify_password(login_data.password, user.password_hash):
            AuditService.log_event(
                db=db,
                event_type="LOGIN_FAILED",
                event_status="FAILED",
                user_id=user.id if user else None,
                details={"attempted_email": login_data.email}
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            AuditService.log_event(
                db=db,
                event_type="UNAUTHORIZED_ACCESS",
                event_status="BLOCKED",
                user_id=user.id,
                details={"reason": "User account deactivated"}
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account has been deactivated by administrator"
            )

        user_roles = [r.name for r in user.roles]
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "roles": user_roles,
            "name": user.name
        }

        access_token = create_access_token(data=token_payload)

        AuditService.log_event(
            db=db,
            event_type="LOGIN_SUCCESS",
            event_status="SUCCESS",
            user_id=user.id,
            details={"roles": user_roles}
        )

        return Token(
            access_token=access_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )
