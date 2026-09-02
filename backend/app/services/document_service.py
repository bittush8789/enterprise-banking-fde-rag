import os
import shutil
import logging
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models import Document, Role, User
from backend.app.schemas.document import DocumentResponse, DocumentUploadResponse
from backend.app.rag.ingestion import DocumentIngestionService
from backend.app.rag.vector_store import vector_store
from backend.app.services.audit_service import AuditService

logger = logging.getLogger("bankassist.document_service")

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}

class DocumentService:
    @staticmethod
    def upload_and_index_document(
        db: Session,
        file: UploadFile,
        document_name: str,
        document_type: str,
        classification: str,
        department: str,
        version: str,
        allowed_roles_names: List[str],
        uploaded_by_user_id: int,
    ) -> DocumentUploadResponse:
        # 1. File validation
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type '{ext}'. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
            )

        # Save to storage
        safe_filename = f"doc_{int(os.path.getmtime(settings.UPLOAD_DIRECTORY) if os.path.exists(settings.UPLOAD_DIRECTORY) else 1)}_{file.filename.replace(' ', '_')}"
        file_dest = os.path.join(settings.UPLOAD_DIRECTORY, safe_filename)

        with open(file_dest, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Validate file size
        file_size_mb = os.path.getsize(file_dest) / (1024 * 1024)
        if file_size_mb > settings.MAX_UPLOAD_SIZE_MB:
            os.remove(file_dest)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File size ({file_size_mb:.2f} MB) exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB} MB."
            )

        # Create Document record
        doc = Document(
            document_name=document_name,
            document_type=document_type,
            classification=classification,
            department=department,
            version=version,
            file_path=file_dest,
            status="PENDING",
            uploaded_by=uploaded_by_user_id,
        )

        # Attach allowed roles
        for rname in allowed_roles_names:
            role = db.query(Role).filter(Role.name == rname.upper()).first()
            if role and role not in doc.allowed_roles:
                doc.allowed_roles.append(role)

        db.add(doc)
        db.commit()
        db.refresh(doc)

        AuditService.log_event(
            db=db,
            event_type="DOCUMENT_UPLOAD",
            event_status="SUCCESS",
            user_id=uploaded_by_user_id,
            details={"document_id": doc.id, "document_name": doc.document_name, "roles": allowed_roles_names}
        )

        # 2. Ingest & Index
        try:
            chunks_count = DocumentIngestionService.ingest_document(db, doc.id)
            AuditService.log_event(
                db=db,
                event_type="DOCUMENT_INDEXED",
                event_status="SUCCESS",
                user_id=uploaded_by_user_id,
                details={"document_id": doc.id, "chunks_indexed": chunks_count}
            )
            return DocumentUploadResponse(
                id=doc.id,
                document_name=doc.document_name,
                status=doc.status,
                chunks_indexed=chunks_count,
                message=f"Document '{doc.document_name}' uploaded and indexed successfully ({chunks_count} chunks)."
            )
        except Exception as e:
            logger.error(f"Error during document ingestion: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Document uploaded but indexing failed: {e}"
            )

    @staticmethod
    def get_documents(db: Session, user_roles: List[str] = None) -> List[Document]:
        # Return all banking documents
        return db.query(Document).order_by(Document.created_at.desc()).all()

    @staticmethod
    def delete_document(db: Session, document_id: int, user_id: int) -> bool:
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

        # Remove from vector store
        vector_store.delete_document_chunks(document_id)

        # Remove file from disk
        if os.path.exists(doc.file_path):
            try:
                os.remove(doc.file_path)
            except Exception as e:
                logger.warning(f"Could not delete physical file: {e}")

        doc_name = doc.document_name
        db.delete(doc)
        db.commit()

        AuditService.log_event(
            db=db,
            event_type="DOCUMENT_DELETED",
            event_status="SUCCESS",
            user_id=user_id,
            details={"document_id": document_id, "document_name": doc_name}
        )
        return True
