from __future__ import annotations

import json
import os

import faiss
import numpy as np

from app.core.config import settings


class SemanticCache:
    def __init__(self, threshold: float = 0.9):
        self.threshold = threshold
        self.index_file = "cache_index.faiss"
        self.query_mapping = "cache_mapping.json"
        self.queries: list = []
        self.index = None
        self._redis = None

        # Redis is optional — silently disabled if not reachable
        try:
            import redis as redis_lib
            client = redis_lib.from_url(settings.REDIS_URL, socket_connect_timeout=1)
            client.ping()
            self._redis = client
        except Exception:
            pass

        if os.path.exists(self.index_file) and os.path.exists(self.query_mapping):
            try:
                self.index = faiss.read_index(self.index_file)
                with open(self.query_mapping) as f:
                    self.queries = json.load(f)
            except Exception:
                self.index = None
                self.queries = []

    def get(self, query_vector, k: int = 1):
        if self._redis is None or self.index is None or self.index.ntotal == 0:
            return None
        try:
            vec = np.array([query_vector]).astype("float32")
            faiss.normalize_L2(vec)
            D, I = self.index.search(vec, k)
            if D[0][0] >= self.threshold and I[0][0] != -1:
                idx = I[0][0]
                if idx < len(self.queries):
                    cached = self._redis.get(self.queries[idx])
                    if cached:
                        return json.loads(cached)
        except Exception:
            pass
        return None

    def set(self, query_vector, query_str: str, result):
        if self._redis is None:
            return
        try:
            query_id = f"cache:{hash(query_str)}"
            self._redis.set(query_id, json.dumps(result), ex=86400)

            vec = np.array([query_vector]).astype("float32")
            faiss.normalize_L2(vec)

            if self.index is None:
                self.index = faiss.IndexFlatIP(len(query_vector))

            self.index.add(vec)
            self.queries.append(query_id)

            faiss.write_index(self.index, self.index_file)
            with open(self.query_mapping, "w") as f:
                json.dump(self.queries, f)
        except Exception:
            pass


semantic_cache = SemanticCache()
