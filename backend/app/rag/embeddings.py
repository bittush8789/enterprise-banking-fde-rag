import logging
from typing import List
import numpy as np
from backend.app.core.config import settings

logger = logging.getLogger("bankassist.embeddings")

class EmbeddingService:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EmbeddingService, cls).__new__(cls)
            cls._instance._initialize_model()
        return cls._instance

    def _initialize_model(self):
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading HuggingFace SentenceTransformer embedding model: {settings.EMBEDDING_MODEL}")
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info("Embedding model loaded successfully.")
        except Exception as e:
            logger.warning(
                f"Could not load SentenceTransformer '{settings.EMBEDDING_MODEL}' ({e}). "
                f"Using lightweight deterministic fallback embedding generator."
            )
            self._model = None

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        if self._model is not None:
            try:
                embeddings = self._model.encode(texts, normalize_embeddings=True)
                return embeddings.tolist()
            except Exception as e:
                logger.error(f"Error generating embeddings with model: {e}")

        # Deterministic lightweight cross-process embedding generator (384-dimensional vector using hashlib)
        import hashlib
        fallback_vectors = []
        for text in texts:
            vec = np.zeros(384, dtype=np.float32)
            # Word token contributions
            words = [w.strip(".,;:!?()[]{}\"'") for w in text.lower().split() if len(w) > 2]
            if not words:
                words = [text.lower().strip()]

            for w in words:
                digest = hashlib.sha256(w.encode("utf-8")).digest()
                # Use digest bytes to seed vector values
                np_seed = int.from_bytes(digest[:4], "big")
                rng = np.random.RandomState(np_seed)
                vec += rng.randn(384).astype(np.float32)

            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            else:
                vec = np.ones(384, dtype=np.float32) / np.sqrt(384)
            fallback_vectors.append(vec.tolist())
        return fallback_vectors

    def get_query_embedding(self, query: str) -> List[float]:
        return self.get_embeddings([query])[0]

embedding_service = EmbeddingService()
