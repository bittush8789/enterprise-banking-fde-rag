import os
import json
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings
from backend.app.core.config import settings

logger = logging.getLogger("bankassist.vector_store")

COLLECTION_NAME = "bank_documents"

class ChromaVectorStore:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaVectorStore, cls).__new__(cls)
            cls._instance._init_chroma()
        return cls._instance

    def _init_chroma(self):
        try:
            if settings.CHROMA_SERVER_HOST:
                logger.info(f"Connecting to remote ChromaDB server at {settings.CHROMA_SERVER_HOST}:{settings.CHROMA_SERVER_PORT}...")
                self.client = chromadb.HttpClient(
                    host=settings.CHROMA_SERVER_HOST,
                    port=settings.CHROMA_SERVER_PORT,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
            else:
                persist_dir = os.path.abspath(settings.CHROMA_PERSIST_DIRECTORY)
                os.makedirs(persist_dir, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )

            self.collection = self.client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )
            logger.info(f"ChromaDB initialized successfully with collection '{COLLECTION_NAME}'")
        except Exception as e:
            logger.error(f"Error initializing ChromaDB client: {e}. Falling back to local PersistentClient.")
            try:
                persist_dir = os.path.abspath(settings.CHROMA_PERSIST_DIRECTORY)
                os.makedirs(persist_dir, exist_ok=True)
                self.client = chromadb.PersistentClient(
                    path=persist_dir,
                    settings=ChromaSettings(anonymized_telemetry=False)
                )
                self.collection = self.client.get_or_create_collection(
                    name=COLLECTION_NAME,
                    metadata={"hnsw:space": "cosine"}
                )
            except Exception as ex:
                logger.error(f"Critical error initializing local fallback ChromaDB: {ex}")
                self.client = None
                self.collection = None

    def add_chunks(
        self,
        chunk_ids: List[str],
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
    ) -> bool:
        if not self.collection:
            logger.warning("ChromaDB collection unavailable.")
            return False

        # Ensure all metadata values are primitive (strings, ints, floats) for ChromaDB
        cleaned_metadatas = []
        for meta in metadatas:
            cleaned = {}
            for k, v in meta.items():
                if isinstance(v, (list, dict)):
                    cleaned[k] = json.dumps(v)
                elif v is None:
                    cleaned[k] = ""
                else:
                    cleaned[k] = v
            cleaned_metadatas.append(cleaned)

        try:
            self.collection.add(
                ids=chunk_ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=cleaned_metadatas,
            )
            logger.info(f"Successfully indexed {len(chunk_ids)} chunks into ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"Failed to add chunks to ChromaDB: {e}")
            return False

    def delete_document_chunks(self, document_id: int) -> bool:
        if not self.collection:
            return False
        try:
            # Delete by metadata filter
            self.collection.delete(where={"document_id": str(document_id)})
            logger.info(f"Deleted chunks for document_id={document_id} from ChromaDB.")
            return True
        except Exception as e:
            logger.error(f"Error deleting chunks for document_id={document_id}: {e}")
            return False

    def query(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        where_filter: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.collection:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

        try:
            kwargs = {
                "query_embeddings": [query_embedding],
                "n_results": n_results,
            }
            if where_filter:
                kwargs["where"] = where_filter

            results = self.collection.query(**kwargs)
            return results
        except Exception as e:
            logger.error(f"ChromaDB query error: {e}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

vector_store = ChromaVectorStore()
