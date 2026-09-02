from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from backend.app.schemas.auth import RoleResponse

class DocumentMetadataCreate(BaseModel):
    document_name: str
    document_type: str
    classification: str = "internal"
    department: str
    version: str = "v1.0"
    allowed_roles: List[str]

class DocumentResponse(BaseModel):
    id: int
    document_name: str
    document_type: str
    classification: str
    department: str
    version: str
    file_path: str
    status: str
    uploaded_by: Optional[int] = None
    created_at: datetime
    allowed_roles: List[RoleResponse] = []

    class Config:
        from_attributes = True

class DocumentUploadResponse(BaseModel):
    id: int
    document_name: str
    status: str
    chunks_indexed: int
    message: str
