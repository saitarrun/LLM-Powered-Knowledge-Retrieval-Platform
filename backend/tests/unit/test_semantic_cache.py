import pytest

from app.services import cache as cache_module


class FakeFaissStore:
    def __init__(self, dimension, index_path):
        self.saved_metadata = None

    def search(self, query_embedding, top_k=1):
        if self.saved_metadata is None:
            return []
        return [{"score": 1.0, "metadata": self.saved_metadata}]

    def add_embeddings(self, embeddings, ids, metadatas=None):
        self.saved_metadata = metadatas[0] if metadatas else {"chunk_id": ids[0]}


@pytest.mark.asyncio
async def test_semantic_cache_round_trips_state_metadata(monkeypatch):
    monkeypatch.setattr(cache_module, "FaissStore", FakeFaissStore)

    cache = cache_module.SemanticCache(dimension=3)
    state = {
        "synthesis_result": {"answer": "cached answer"},
        "rewritten_query": "rewritten",
    }

    cache.add([0.1, 0.2, 0.3], state)

    assert await cache.check([0.1, 0.2, 0.3]) == {
        "synthesis_result": {"answer": "cached answer"},
        "rewritten_query": "rewritten",
        "cached": True,
    }
