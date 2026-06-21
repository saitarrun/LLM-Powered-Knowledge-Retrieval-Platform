from __future__ import annotations

from sentence_transformers import SentenceTransformer

from app.core.config import settings
from app.core.logging import logger

import asyncio

# Serialize all model.encode() calls — SentenceTransformer is not thread-safe
_embed_lock = asyncio.Lock()


class EmbeddingService:
    def __init__(self):
        logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(settings.EMBEDDING_MODEL, device="cpu")
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts (called from sync context)."""
        if not texts:
            return []
        embeddings = self.model.encode(texts)
        return embeddings.tolist() if hasattr(embeddings, "tolist") else embeddings

    def embed_one(self, text: str) -> list[float]:
        """Generate embedding for a single text (called from sync context)."""
        embedding = self.model.encode([text])
        result = embedding.tolist() if hasattr(embedding, "tolist") else embedding
        return result[0] if isinstance(result, list) and len(result) > 0 else result

    async def embed_one_async(self, text: str) -> list[float]:
        """Thread-safe async wrapper — serializes concurrent calls."""
        async with _embed_lock:
            return await asyncio.to_thread(self.embed_one, text)

    async def embed_async(self, texts: list[str]) -> list[list[float]]:
        """Thread-safe async wrapper for batch embedding."""
        async with _embed_lock:
            return await asyncio.to_thread(self.embed, texts)


embedding_service = EmbeddingService()
