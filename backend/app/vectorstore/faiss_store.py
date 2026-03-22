import numpy as np
import faiss
import os
import pickle

class FaissStore:
    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        self.index = faiss.IndexFlatIP(dimension)
        self.metadatas = []
        self.load()

    def add_embeddings(self, embeddings: list[list[float]], metadatas: list[dict]):
        embeddings_np = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings_np)
        self.index.add(embeddings_np)
        self.metadatas.extend(metadatas)
        self.save()

    def search(self, query_embedding: list[float], top_k: int = 5):
        query_np = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_np)
        scores, indices = self.index.search(query_np, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx != -1:
                results.append({"score": float(scores[0][i]), "metadata": self.metadatas[idx]})
        return results

    def save(self):
        faiss.write_index(self.index, self.index_path)
        with open(f"{self.index_path}_meta.pkl", "wb") as f:
            pickle.dump(self.metadatas, f)

    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            with open(f"{self.index_path}_meta.pkl", "rb") as f:
                self.metadatas = pickle.load(f)
