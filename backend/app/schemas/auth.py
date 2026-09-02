from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr

class RoleResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        from_attributes = True

class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    roles: Optional[List[str]] = ["CUSTOMER_SUPPORT"]

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    is_active: bool
    roles: List[RoleResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True

Token.model_rebuild()
