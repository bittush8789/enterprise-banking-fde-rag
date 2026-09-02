import os
import json
import math
import logging
from typing import List, Dict, Any, Optional

from backend.app.core.config import settings

logger = logging.getLogger("bankassist.vector_store")

INDEX_NAME = settings.PINECONE_INDEX_NAME
EMBEDDING_DIMENSION = 384  # BAAI/bge-small-en-v1.5 dimension


class InMemoryPineconeFallback:
    """Local high-performance in-memory vector store matching Pinecone's interface for offline & test environments."""
    def __init__(self):
        self.vectors: Dict[str, Dict[str, Any]] = {}

    def upsert(self, vectors: List[Dict[str, Any]]):
        for v in vectors:
            self.vectors[v["id"]] = {
                "id": v["id"],
                "values": v["values"],
                "metadata": v.get("metadata", {})
            }

    def delete(self, filter: Optional[Dict[str, Any]] = None, ids: Optional[List[str]] = None):
        if ids:
            for vid in ids:
                self.vectors.pop(vid, None)
        elif filter:
            keys_to_delete = []
            for vid, data in self.vectors.items():
                meta = data.get("metadata", {})
                match = True
                for fk, fv in filter.items():
                    if meta.get(fk) != fv:
                        match = False
                        break
                if match:
                    keys_to_delete.append(vid)
            for k in keys_to_delete:
                self.vectors.pop(k, None)

    def query(self, vector: List[float], top_k: int = 5, filter: Optional[Dict[str, Any]] = None, include_metadata: bool = True):
        scored_matches = []
        
        def cosine_similarity(v1: List[float], v2: List[float]) -> float:
            dot = sum(a * b for a, b in zip(v1, v2))
            norm1 = math.sqrt(sum(a * a for a in v1)) or 1e-10
            norm2 = math.sqrt(sum(b * b for b in v2)) or 1e-10
            return dot / (norm1 * norm2)

        for vid, data in self.vectors.items():
            meta = data.get("metadata", {})
            if filter:
                match = True
                for fk, fv in filter.items():
                    if meta.get(fk) != fv:
                        match = False
                        break
                if not match:
                    continue

            score = cosine_similarity(vector, data["values"])
            scored_matches.append({
                "id": vid,
                "score": score,
                "metadata": meta if include_metadata else {}
            })

        scored_matches.sort(key=lambda x: x["score"], reverse=True)
        return {"matches": scored_matches[:top_k]}


class PineconeVectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PineconeVectorStore, cls).__new__(cls)
            cls._instance._init_pinecone()
        return cls._instance

    def _init_pinecone(self):
        self.pc = None
        self.index = None
        self.is_remote = False

        if settings.PINECONE_API_KEY and settings.PINECONE_API_KEY.strip() and not settings.PINECONE_API_KEY.startswith("your_"):
            try:
                from pinecone import Pinecone, ServerlessSpec
                logger.info("Initializing Pinecone client with API key...")
                self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
                
                # Check if index exists, create if not
                existing_indexes = [idx.name for idx in self.pc.list_indexes()]
                if INDEX_NAME not in existing_indexes:
                    logger.info(f"Creating Pinecone serverless index '{INDEX_NAME}' (dim={EMBEDDING_DIMENSION}, metric=cosine)...")
                    self.pc.create_index(
                        name=INDEX_NAME,
                        dimension=EMBEDDING_DIMENSION,
                        metric="cosine",
                        spec=ServerlessSpec(
                            cloud=settings.PINECONE_CLOUD,
                            region=settings.PINECONE_REGION
                        )
                    )
                self.index = self.pc.Index(INDEX_NAME)
                self.is_remote = True
                logger.info(f"Connected to remote Pinecone index: '{INDEX_NAME}'")
                return
            except Exception as e:
                logger.warning(f"Could not connect to remote Pinecone: {e}. Utilizing high-performance in-memory vector fallback.")

        logger.info("Operating with Pinecone-compatible local vector engine.")
        self.index = InMemoryPineconeFallback()

    def add_chunks(
        self,
        chunk_ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> bool:
        if not self.index:
            logger.warning("Pinecone index unavailable.")
            return False

        try:
            vectors_to_upsert = []
            for cid, doc_text, emb, meta in zip(chunk_ids, documents, embeddings, metadatas):
                # Clean metadata for Pinecone
                cleaned_meta = dict(meta)
                cleaned_meta["text"] = doc_text
                # Convert complex objects to JSON strings
                for k, v in list(cleaned_meta.items()):
                    if isinstance(v, (list, dict)):
                        cleaned_meta[k] = json.dumps(v)
                    elif v is None:
                        cleaned_meta[k] = ""

                vectors_to_upsert.append({
                    "id": cid,
                    "values": emb,
                    "metadata": cleaned_meta
                })

            # Upsert in batches of 100
            batch_size = 100
            for i in range(0, len(vectors_to_upsert), batch_size):
                batch = vectors_to_upsert[i:i + batch_size]
                self.index.upsert(vectors=batch)

            logger.info(f"Successfully upserted {len(chunk_ids)} chunks into Pinecone index '{INDEX_NAME}'.")
            return True
        except Exception as e:
            logger.error(f"Failed to upsert chunks into Pinecone: {e}")
            return False

    def delete_document_chunks(self, document_id: int) -> bool:
        if not self.index:
            return False
        try:
            self.index.delete(filter={"document_id": str(document_id)})
            logger.info(f"Deleted chunks for document_id={document_id} from Pinecone.")
            return True
        except Exception as e:
            logger.error(f"Error deleting chunks for document_id={document_id} from Pinecone: {e}")
            return False

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Queries Pinecone and formats return value to standard format {ids, documents, metadatas, distances}."""
        if not self.index:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        try:
            res = self.index.query(
                vector=query_embedding,
                top_k=n_results,
                filter=where_filter,
                include_metadata=True
            )

            matches = res.get("matches", [])
            ids = [m["id"] for m in matches]
            docs = [m.get("metadata", {}).get("text", "") for m in matches]
            metadatas = [m.get("metadata", {}) for m in matches]
            
            # Pinecone score is cosine similarity (1.0 = identical).
            # Convert cosine similarity to cosine distance (1.0 - similarity)
            distances = [max(0.0, 1.0 - float(m.get("score", 0.0))) for m in matches]

            return {
                "ids": [ids],
                "documents": [docs],
                "metadatas": [metadatas],
                "distances": [distances]
            }
        except Exception as e:
            logger.error(f"Pinecone query error: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


vector_store = PineconeVectorStore()
ChromaVectorStore = PineconeVectorStore  # Alias for backward compatibility
