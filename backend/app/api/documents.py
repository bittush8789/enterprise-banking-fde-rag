import json
from typing import List
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.database import get_db
from backend.app.core.security import get_current_user_payload, require_roles
from backend.app.models import Document
from backend.app.schemas.document import DocumentResponse, DocumentUploadResponse
from backend.app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["Document Management"])

@router.post("/upload", response_model=DocumentUploadResponse)
def upload_document(
    file: UploadFile = File(...),
    document_name: str = Form(...),
    document_type: str = Form(...),
    classification: str = Form("internal"),
    department: str = Form(...),
    version: str = Form("v1.0"),
    allowed_roles: str = Form("[]"),
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Upload and index a banking policy or SOP document.
    """
    user_id = int(payload.get("sub"))
    try:
        roles_list = json.loads(allowed_roles) if isinstance(allowed_roles, str) else allowed_roles
        if not isinstance(roles_list, list):
            roles_list = [str(roles_list)]
    except Exception:
        roles_list = [r.strip() for r in allowed_roles.split(",") if r.strip()]

    return DocumentService.upload_and_index_document(
        db=db,
        file=file,
        document_name=document_name,
        document_type=document_type,
        classification=classification,
        department=department,
        version=version,
        allowed_roles_names=roles_list,
        uploaded_by_user_id=user_id
    )

@router.get("", response_model=List[DocumentResponse])
def get_all_documents(
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    List all banking documents.
    """
    user_roles = payload.get("roles", [])
    docs = DocumentService.get_documents(db, user_roles)
    return [DocumentResponse.from_orm(d) for d in docs]

@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_details(
    document_id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Get detailed metadata for a single document.
    """
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return DocumentResponse.from_orm(doc)

@router.delete("/{document_id}")
def delete_document(
    document_id: int,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db)
):
    """
    Delete a document and purge its vector chunks from ChromaDB.
    """
    user_id = int(payload.get("sub"))
    DocumentService.delete_document(db, document_id, user_id)
    return {"success": True, "message": f"Document ID {document_id} deleted successfully."}
