import numpy as np
import faiss
import os
import pickle

class FaissStore:
    def __init__(self, dimension: int, index_path: str):
        self.dimension = dimension
        self.index_path = index_path
        # Use IndexIDMap to support deletion by ID
        self.index = faiss.IndexIDMap(faiss.IndexFlatIP(dimension))
        self.metadatas = {}  # Changed to dict: faiss_id -> metadata
        self.chunk_id_to_faiss_id = {}  # Map chunk IDs to FAISS IDs
        self.next_id = 0
        self.load()

    def add_embeddings(self, embeddings: list[list[float]], ids: list[str], metadatas: list[dict] | None = None):
        if metadatas is not None and len(metadatas) != len(ids):
            raise ValueError("metadatas length must match ids length")

        embeddings_np = np.array(embeddings).astype('float32')
        faiss.normalize_L2(embeddings_np)

        # Create FAISS IDs for each embedding
        faiss_ids = np.arange(self.next_id, self.next_id + len(embeddings), dtype=np.int64)

        # Add to FAISS index with IDs
        self.index.add_with_ids(embeddings_np, faiss_ids)

        # Store metadata and mapping
        for i, chunk_id in enumerate(ids):
            faiss_id = int(faiss_ids[i])
            self.metadatas[faiss_id] = metadatas[i] if metadatas is not None else {"chunk_id": chunk_id}
            self.chunk_id_to_faiss_id[chunk_id] = faiss_id

        self.next_id += len(embeddings)
        self.save()

    def search(self, query_embedding: list[float], top_k: int = 5):
        query_np = np.array([query_embedding]).astype('float32')
        faiss.normalize_L2(query_np)
        scores, indices = self.index.search(query_np, top_k)

        results = []
        for i, idx in enumerate(indices[0]):
            idx = int(idx)
            if idx != -1 and idx in self.metadatas:
                results.append({
                    "score": float(scores[0][i]),
                    "metadata": self.metadatas[idx]
                })
        return results

    def remove(self, chunk_ids: list[str]):
        """Remove embeddings by chunk ID."""
        faiss_ids = []
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_id_to_faiss_id:
                faiss_id = self.chunk_id_to_faiss_id[chunk_id]
                faiss_ids.append(faiss_id)
                del self.metadatas[faiss_id]
                del self.chunk_id_to_faiss_id[chunk_id]

        if faiss_ids:
            faiss_ids_np = np.array(faiss_ids, dtype=np.int64)
            self.index.remove_ids(faiss_ids_np)
            self.save()

    def save(self):
        faiss.write_index(self.index, self.index_path)
        state = {
            "metadatas": self.metadatas,
            "chunk_id_to_faiss_id": self.chunk_id_to_faiss_id,
            "next_id": self.next_id
        }
        with open(f"{self.index_path}_state.pkl", "wb") as f:
            pickle.dump(state, f)

    def load(self):
        if os.path.exists(self.index_path):
            self.index = faiss.read_index(self.index_path)
            # Convert to IndexIDMap if it isn't already
            if not isinstance(self.index, faiss.IndexIDMap):
                index_flat = self.index
                self.index = faiss.IndexIDMap(index_flat)

            state_path = f"{self.index_path}_state.pkl"
            if os.path.exists(state_path):
                with open(state_path, "rb") as f:
                    state = pickle.load(f)
                    self.metadatas = {
                        int(faiss_id): metadata
                        for faiss_id, metadata in state.get("metadatas", {}).items()
                    }
                    self.chunk_id_to_faiss_id = {
                        chunk_id: int(faiss_id)
                        for chunk_id, faiss_id in state.get("chunk_id_to_faiss_id", {}).items()
                    }
                    self.next_id = state.get("next_id", 0)
