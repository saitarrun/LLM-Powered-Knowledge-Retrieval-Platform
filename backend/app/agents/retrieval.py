from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState
from app.vectorstore.hybrid_store import HybridStore, hybrid_store
import asyncio
from app.graph.extractor import graph_extractor


class RetrievalAgent(BaseAgent):
    name = "retrieval"

    def __init__(self, store: HybridStore | None = None) -> None:
        self._store = store or hybrid_store

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        query = state.rewritten_query or state.query
        variations = state.query_variations or [query]
        fetch_k = state.config.top_k * max(
            int(state.config.filters.get("overfetch_multiplier") or 2), 1
        )

        if not query:
            state.retrieved_candidates = []
            return state, TraceEvent(
                agent=self.name, action="retrieve", result="No query provided."
            )

        try:
            candidates = await self._store.search_multi(variations, top_k=fetch_k)
        except Exception as e:
            logger.error(f"Vector retrieval error: {e}")
            state.retrieved_candidates = []
            return state, TraceEvent(
                agent=self.name, action="retrieve", result=f"Retrieval failed: {e}"
            )

        # Graph retrieval is best-effort — skip if Neo4j is unavailable or slow
        try:
            graph_results = await asyncio.wait_for(
                graph_extractor.query_graph(query), timeout=8.0
            )
            for gr in graph_results:
                candidates.append({
                    "score": 1.0,
                    "metadata": {"chunk_id": "graph_node"},
                    "text": f"Knowledge Graph Context: {gr}",
                })
        except Exception as e:
            logger.warning(f"Graph retrieval skipped: {e}")

        state.retrieved_candidates = candidates
        logger.info(
            f"Hybrid RRF retrieved {len(candidates) - len(graph_results)} chunks + {len(graph_results)} graph edges "
            f"from {len(variations)} variations for: {query}"
        )

        return state, TraceEvent(
            agent=self.name,
            action="retrieve",
            result=f"Found {len(candidates)} candidates via hybrid RRF ({len(variations)} variations).",
        )
