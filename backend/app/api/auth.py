from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_payload
from backend.app.models import User
from backend.app.schemas.auth import UserRegister, UserLogin, Token, UserResponse
from backend.app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new banking employee user account.
    """
    return AuthService.register_user(db, user_in)

@router.post("/login", response_model=Token)
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and issue JWT access token.
    """
    return AuthService.authenticate_user(db, login_data)

@router.get("/me", response_model=UserResponse)
def get_current_user(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Retrieve logged-in user details and assigned roles.
    """
    user_id = int(payload.get("sub"))
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserResponse.from_orm(user)
