import os
import re
import json
import logging
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models import Document, Role, document_permissions
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.vector_store import vector_store
from backend.app.guardrails.pii_masker import PIIMasker

logger = logging.getLogger("bankassist.ingestion")

class TextSplitter:
    """
    Recursive character text splitter with configurable chunk size and overlap.
    """
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, separators: List[str] = None):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", ". ", " ", ""]

    def split_text(self, text: str) -> List[str]:
        if not text:
            return []

        chunks = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = start + self.chunk_size
            if end >= text_len:
                chunk = text[start:]
                if chunk.strip():
                    chunks.append(chunk.strip())
                break

            # Try to find natural break point
            best_split = end
            for sep in self.separators:
                if sep == "":
                    break
                idx = text.rfind(sep, start + int(self.chunk_size * 0.5), end)
                if idx != -1:
                    best_split = idx + len(sep)
                    break

            chunk = text[start:best_split].strip()
            if chunk:
                chunks.append(chunk)

            # Move start forward by chunk size minus overlap
            start = max(start + 1, best_split - self.chunk_overlap)

        return chunks

class DocumentIngestionService:
    @staticmethod
    def extract_text(file_path: str) -> List[Tuple[int, str]]:
        """
        Extracts text from file.
        Returns a list of tuples: (page_number, text_content)
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()
        pages = []

        if ext == ".pdf":
            try:
                import pypdf
                reader = pypdf.PdfReader(file_path)
                for idx, page in enumerate(reader.pages):
                    page_text = page.extract_text() or ""
                    pages.append((idx + 1, page_text))
            except Exception as e:
                logger.error(f"Error reading PDF {file_path}: {e}")
                raise ValueError(f"Failed to parse PDF document: {e}")

        elif ext == ".docx":
            try:
                import docx
                doc = docx.Document(file_path)
                full_text = "\n".join([p.text for p in doc.paragraphs if p.text])
                pages.append((1, full_text))
            except Exception as e:
                logger.error(f"Error reading DOCX {file_path}: {e}")
                raise ValueError(f"Failed to parse DOCX document: {e}")

        elif ext in [".txt", ".md", ".json"]:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                pages.append((1, content))
            except Exception as e:
                logger.error(f"Error reading text file {file_path}: {e}")
                raise ValueError(f"Failed to read text file: {e}")
        else:
            raise ValueError(f"Unsupported file format: {ext}")

        return pages

    @classmethod
    def ingest_document(
        cls,
        db: Session,
        document_id: int,
    ) -> int:
        """
        Extracts, splits, embeds, and indexes document into ChromaDB.
        """
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise ValueError(f"Document with ID {document_id} not found.")

        doc.status = "INDEXING"
        db.commit()

        try:
            pages = cls.extract_text(doc.file_path)
            splitter = TextSplitter(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP
            )

            chunk_ids = []
            documents_text = []
            metadatas = []

            # Extract allowed role names
            allowed_role_names = [role.name for role in doc.allowed_roles]
            # Ensure ADMIN always has access
            if "ADMIN" not in allowed_role_names:
                allowed_role_names.append("ADMIN")

            allowed_roles_json = json.dumps(allowed_role_names)

            chunk_index = 0
            for page_num, page_content in pages:
                # Pre-screen and mask sensitive PII if present in raw document
                masked_page_content, _ = PIIMasker.mask_text(page_content)
                chunks = splitter.split_text(masked_page_content)

                for chunk in chunks:
                    chunk_index += 1
                    cid = f"doc_{doc.id}_chunk_{chunk_index}"
                    
                    # Extract approximate section header if present
                    first_line = chunk.split("\n")[0][:100]

                    chunk_ids.append(cid)
                    documents_text.append(chunk)
                    metadatas.append({
                        "document_id": str(doc.id),
                        "document_name": doc.document_name,
                        "document_type": doc.document_type,
                        "classification": doc.classification,
                        "department": doc.department,
                        "version": doc.version,
                        "page_number": page_num,
                        "section": first_line,
                        "allowed_roles": allowed_roles_json,
                    })

            if documents_text:
                # Compute embeddings in batch
                embeddings = embedding_service.get_embeddings(documents_text)

                # Delete any old chunks for this document before re-indexing
                vector_store.delete_document_chunks(doc.id)

                # Insert into ChromaDB
                vector_store.add_chunks(
                    chunk_ids=chunk_ids,
                    documents=documents_text,
                    embeddings=embeddings,
                    metadatas=metadatas
                )

            doc.status = "INDEXED"
            db.commit()
            logger.info(f"Document {doc.document_name} indexed with {len(chunk_ids)} chunks.")
            return len(chunk_ids)

        except Exception as e:
            doc.status = "FAILED"
            db.commit()
            logger.error(f"Failed to index document {doc.id}: {e}")
            raise e
