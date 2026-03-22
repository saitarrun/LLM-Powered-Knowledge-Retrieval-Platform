import os
import pickle
from rank_bm25 import BM25Okapi

class BM25Store:
    def __init__(self, index_path: str):
        self.index_path = index_path
        self.corpus = []
        self.metadatas = []
        self.bm25 = None
        self.load()

    def add_texts(self, texts: list[str], metadatas: list[dict]):
        self.corpus.extend(texts)
        self.metadatas.extend(metadatas)
        tokenized_corpus = [doc.lower().split(" ") for doc in self.corpus]
        self.bm25 = BM25Okapi(tokenized_corpus)
        self.save()

    def search(self, query: str, top_k: int = 5):
        if not self.bm25: return []
        tokenized_query = query.lower().split(" ")
        doc_scores = self.bm25.get_scores(tokenized_query)
        top_n = sorted(range(len(doc_scores)), key=lambda i: doc_scores[i], reverse=True)[:top_k]
        return [{"score": float(doc_scores[i]), "metadata": self.metadatas[i], "text": self.corpus[i]} for i in top_n if doc_scores[i] > 0]

    def save(self):
        with open(self.index_path, "wb") as f:
            pickle.dump({"corpus": self.corpus, "metadatas": self.metadatas}, f)

    def load(self):
        if os.path.exists(self.index_path):
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
                self.corpus = data.get("corpus", [])
                self.metadatas = data.get("metadatas", [])
                if self.corpus:
                    tokenized_corpus = [doc.lower().split(" ") for doc in self.corpus]
                    self.bm25 = BM25Okapi(tokenized_corpus)
