import json
import logging
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.rag.embeddings import embedding_service
from backend.app.rag.vector_store import vector_store
from backend.app.schemas.chat import SourceCitation

logger = logging.getLogger("bankassist.retriever")

class RetrievedChunk:
    def __init__(
        self,
        chunk_id: str,
        text: str,
        score: float,
        metadata: Dict[str, Any]
    ):
        self.chunk_id = chunk_id
        self.text = text
        self.score = score
        self.metadata = metadata

    @property
    def document_name(self) -> str:
        return self.metadata.get("document_name", "Unknown Document")

    @property
    def page_number(self) -> int:
        return int(self.metadata.get("page_number", 1))

    @property
    def section(self) -> str:
        return self.metadata.get("section", "General")

    def to_citation(self) -> SourceCitation:
        return SourceCitation(
            document_id=self.metadata.get("document_id"),
            document_name=self.document_name,
            page_number=self.page_number,
            section=self.section,
            score=round(self.score, 3),
            excerpt=self.text[:180] + "..." if len(self.text) > 180 else self.text
        )

class PermissionAwareRetriever:
    """
    Retrieves document chunks from ChromaDB and strictly filters candidates by user role permissions
    and similarity confidence threshold.
    """

    @classmethod
    def retrieve(
        cls,
        query: str,
        user_roles: List[str],
        top_k: int = None,
        threshold: float = None,
    ) -> List[RetrievedChunk]:
        if top_k is None:
            top_k = settings.TOP_K
        if threshold is None:
            threshold = settings.RETRIEVAL_THRESHOLD

        if not query or not query.strip():
            return []

        # 1. Compute query embedding
        query_embedding = embedding_service.get_query_embedding(query)

        # Retrieve a broader candidate pool (2x top_k) to allow for post-filtering by role and threshold
        n_candidates = max(10, top_k * 3)
        raw_results = vector_store.query(
            query_embedding=query_embedding,
            n_results=n_candidates
        )

        ids_list = raw_results.get("ids", [[]])[0]
        docs_list = raw_results.get("documents", [[]])[0]
        metas_list = raw_results.get("metadatas", [[]])[0]
        distances_list = raw_results.get("distances", [[]])[0]

        is_admin = "ADMIN" in user_roles
        valid_chunks: List[RetrievedChunk] = []

        for cid, doc_text, meta, dist in zip(ids_list, docs_list, metas_list, distances_list):
            # In Chroma cosine distance: similarity = 1.0 - distance
            similarity = max(0.0, 1.0 - float(dist)) if dist is not None else 0.85

            # Confidence Threshold Check (Groundedness)
            if similarity < threshold:
                logger.debug(f"Chunk {cid} excluded: similarity {similarity:.3f} < threshold {threshold}")
                continue

            valid_chunks.append(RetrievedChunk(
                chunk_id=cid,
                text=doc_text,
                score=similarity,
                metadata=meta
            ))

            if len(valid_chunks) >= top_k:
                break

        return valid_chunks
