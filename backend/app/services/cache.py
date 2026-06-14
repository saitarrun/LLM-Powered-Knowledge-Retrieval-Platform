import json
from typing import Any
from uuid import uuid4

from app.core.config import settings
from app.vectorstore.faiss_store import FaissStore


class SemanticCache:
    def __init__(self, dimension: int):
        self.store = FaissStore(dimension=dimension, index_path=settings.SEMANTIC_CACHE_PATH)
        self.threshold = settings.SEMANTIC_CACHE_THRESHOLD

    async def check(self, query_embedding: list[float]) -> dict[str, Any] | None:
        results = self.store.search(query_embedding, top_k=1)
        if not results:
            return None
        best_match = results[0]
        if best_match["score"] >= self.threshold:
            state_json = best_match["metadata"].get("state_json")
            return json.loads(state_json) if state_json else None
        return None

    def add(self, query_embedding: list[float], state: dict[str, Any]):
        cache_data = {
            "synthesis_result": state.get("synthesis_result"),
            "rewritten_query": state.get("rewritten_query"),
            "cached": True,
        }
        metadata = {"state_json": json.dumps(cache_data)}
        self.store.add_embeddings(
            [query_embedding],
            [f"cache:{uuid4()}"],
            metadatas=[metadata],
        )
