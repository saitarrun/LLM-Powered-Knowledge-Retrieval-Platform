from __future__ import annotations

"""
Single shared HybridStore instance that wraps FAISS (dense) and BM25 (sparse).

All callers — RetrievalAgent, IngestionPipeline, approval routes — import
`hybrid_store` from here so they share one in-memory cache against the same
index files. Multiple instances reading from the same files would each hold
stale caches invisible to the others.
"""

import asyncio

from app.core.config import settings
from app.core.logging import logger
from app.services.embedding import embedding_service
from app.vectorstore.bm25_store import BM25Store
from app.vectorstore.faiss_store import FaissStore

_RRF_K = 60


class HybridStore:
    """Dense + sparse retrieval with Reciprocal Rank Fusion."""

    def __init__(self, faiss: FaissStore, bm25: BM25Store) -> None:
        self._faiss = faiss
        self._bm25 = bm25

    # ── write side ────────────────────────────────────────────────────────────

    def add(
        self,
        texts: list[str],
        ids: list[str],
        embeddings: list[list[float]] | None = None,
        metadatas: list[dict] | None = None,
    ) -> None:
        if embeddings is None:
            embeddings = embedding_service.embed(texts)
        metadatas = metadatas or [{"chunk_id": cid} for cid in ids]
        self._faiss.add_embeddings(embeddings, ids, metadatas)
        self._bm25.add_texts(texts, metadatas)

    def remove(self, ids: list[str]) -> None:
        self._faiss.remove(ids)
        # BM25 has no delete; rebuild on next add via its internal reload.

    # ── read side ─────────────────────────────────────────────────────────────

    async def search_multi(
        self,
        query_variations: list[str],
        top_k: int = 5,
    ) -> list[dict]:
        """
        Run FAISS + BM25 for every query variation in parallel, fuse ranks with RRF,
        return top_k results sorted by fused score.

        Each variation fans out into two concurrent thread-pool calls (FAISS + BM25).
        All variations run concurrently via asyncio.gather, so N variations × 2 stores
        = 2N tasks in flight instead of sequential.
        """
        async def _search_variation(variation: str) -> tuple[list[dict], list[dict]]:
            embedding = await asyncio.to_thread(embedding_service.embed_one, variation)
            faiss_res, bm25_res = await asyncio.gather(
                asyncio.to_thread(self._faiss.search, embedding, top_k),
                asyncio.to_thread(self._bm25.search, variation, top_k),
            )
            return faiss_res, bm25_res

        per_variation = await asyncio.gather(*(_search_variation(v) for v in query_variations))

        rrf_scores: dict[str, float] = {}
        chunk_metadata: dict[str, dict] = {}
        for faiss_res, bm25_res in per_variation:
            _apply_rrf(faiss_res, rrf_scores, chunk_metadata)
            _apply_rrf(bm25_res, rrf_scores, chunk_metadata)

        sorted_chunks = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        return [
            {"score": score, "metadata": chunk_metadata[chunk_id]}
            for chunk_id, score in sorted_chunks[:top_k]
        ]

    async def search(
        self,
        query_text: str = "",
        query_embedding: list[float] | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """Single-query search — satisfies the VectorStore protocol."""
        return await self.search_multi([query_text], top_k=top_k)


def _apply_rrf(
    results: list[dict],
    rrf_scores: dict[str, float],
    chunk_metadata: dict[str, dict],
) -> None:
    for rank, result in enumerate(results):
        chunk_id = result["metadata"].get("chunk_id")
        if not chunk_id:
            continue
        rrf_scores[chunk_id] = rrf_scores.get(chunk_id, 0.0) + 1.0 / (_RRF_K + rank + 1)
        chunk_metadata[chunk_id] = result["metadata"]


def _make_hybrid_store() -> HybridStore:
    try:
        faiss = FaissStore(
            dimension=embedding_service.dimension,
            index_path=settings.FAISS_INDEX_PATH,
        )
        bm25 = BM25Store(index_path=settings.BM25_INDEX_PATH)
        logger.info("HybridStore initialised (FAISS + BM25)")
        return HybridStore(faiss, bm25)
    except Exception as exc:
        logger.warning(f"HybridStore init failed: {exc} — retrieval will be degraded")
        raise


hybrid_store: HybridStore = _make_hybrid_store()
