from typing import List
from sentence_transformers import SentenceTransformer
from app.core.config import settings
from app.core.logging import logger


class EmbeddingService:
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL)
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")

    def embed(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        if not texts:
            return []
        embeddings = self.model.encode(texts, convert_to_numpy=False)
        return embeddings.tolist() if hasattr(embeddings, 'tolist') else embeddings

    def embed_one(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self.model.encode([text], convert_to_numpy=False)
        result = embedding.tolist() if hasattr(embedding, 'tolist') else embedding
        return result[0] if isinstance(result, list) and len(result) > 0 else result


embedding_service = EmbeddingService()
