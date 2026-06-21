from __future__ import annotations

import asyncio

from sentence_transformers import CrossEncoder

from app.agents.base import BaseAgent
from app.core.config import settings
from app.core.logging import logger
from app.db.repositories import ChunkRepository, chunk_repository
from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState


class EvidenceAgent(BaseAgent):
    name = "evidence"

    def __init__(
        self,
        reranker: CrossEncoder | None = None,
        repo: ChunkRepository | None = None,
    ) -> None:
        logger.info(f"Loading CrossEncoder: {settings.RERANKING_MODEL}")
        self.reranker = reranker or CrossEncoder(settings.RERANKING_MODEL, device="cpu")
        self._repo = repo or chunk_repository

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        query = state.rewritten_query or state.query
        candidates = state.retrieved_candidates
        top_k = state.config.top_k
        filters = state.config.filters
        db = state.db

        if not candidates:
            state.reranked_chunks = []
            return state, TraceEvent(agent=self.name, action="rerank", result="No candidates.")

        chunk_ids = [c["metadata"]["chunk_id"] for c in candidates]
        document_filters_present = any(
            key in filters
            for key in [
                "document_ids",
                "filename_contains",
                "status",
                "approval_required",
                "approved_by",
                "created_after",
                "created_before",
            ]
        )

        chunk_map: dict = {}
        if db is not None:
            db_chunks = self._repo.fetch_chunks(db, chunk_ids, filters)
            chunk_map = {c.id: c for c in db_chunks}

        valid_candidates = []
        pairs = []
        for c in candidates:
            chunk_id = c["metadata"]["chunk_id"]
            if document_filters_present and chunk_id not in chunk_map and chunk_id != "graph_node":
                continue
            txt = chunk_map[chunk_id].text if chunk_id in chunk_map else c.get("text")
            if txt:
                pairs.append((query, txt))
                valid_candidates.append(
                    {
                        "score": c["score"],
                        "metadata": c["metadata"],
                        "text": txt,
                        "db_chunk": chunk_map.get(chunk_id),
                    }
                )

        if not pairs:
            state.reranked_chunks = valid_candidates[:top_k]
            return state, TraceEvent(agent=self.name, action="skip_rerank", result="No pairs.")

        scores = await asyncio.to_thread(self.reranker.predict, pairs)
        for i, score in enumerate(scores):
            valid_candidates[i]["rerank_score"] = float(score)

        valid_candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        has_explicit_threshold = "min_rerank_score" in filters
        min_rerank_score = float(filters.get("min_rerank_score", -5.0))
        final_chunks = [
            c for c in valid_candidates[:top_k] if c.get("rerank_score", 0) >= min_rerank_score
        ]
        state.reranked_chunks = (
            final_chunks
            if has_explicit_threshold
            else (final_chunks or valid_candidates[:top_k])
        )

        return state, TraceEvent(
            agent=self.name,
            action="rerank",
            result=f"Selected {len(state.reranked_chunks)} chunks.",
        )


evidence_agent = EvidenceAgent()
