from __future__ import annotations

import json
import os
import faiss
import numpy as np
import redis
from app.core.config import settings

class SemanticCache:
    def __init__(self, threshold=0.9):
        self.threshold = threshold
        self.redis_client = redis.from_url(settings.REDIS_URL)
        self.index_file = "cache_index.faiss"
        self.query_mapping = "cache_mapping.json"
        
        self.queries = []
        if os.path.exists(self.index_file) and os.path.exists(self.query_mapping):
            try:
                self.index = faiss.read_index(self.index_file)
                with open(self.query_mapping, "r") as f:
                    self.queries = json.load(f)
            except Exception:
                self.index = None
                self.queries = []
        else:
            self.index = None

    def get(self, query_vector, k=1):
        if self.index is None or self.index.ntotal == 0:
            return None
        
        vec = np.array([query_vector]).astype("float32")
        faiss.normalize_L2(vec)
        D, I = self.index.search(vec, k)
        
        if D[0][0] >= self.threshold and I[0][0] != -1:
            idx = I[0][0]
            if idx < len(self.queries):
                query_id = self.queries[idx]
                cached_result = self.redis_client.get(query_id)
                if cached_result:
                    return json.loads(cached_result)
        return None

    def set(self, query_vector, query_str, result):
        query_id = f"cache:{hash(query_str)}"
        self.redis_client.set(query_id, json.dumps(result), ex=86400) # 24h expiration
        
        vec = np.array([query_vector]).astype("float32")
        faiss.normalize_L2(vec)
        
        if self.index is None:
            self.index = faiss.IndexFlatIP(len(query_vector))
            
        self.index.add(vec)
        self.queries.append(query_id)
        
        faiss.write_index(self.index, self.index_file)
        with open(self.query_mapping, "w") as f:
            json.dump(self.queries, f)

semantic_cache = SemanticCache()
