from typing import Dict, Any, Tuple
from app.agents.base import BaseAgent
from app.schemas.models import TraceEvent
from app.services.embedding import embedding_service
from app.vectorstore.faiss_store import FaissStore
from app.core.config import settings
from app.core.logging import logger


class RetrievalAgent(BaseAgent):
    name = "retrieval"

    def __init__(self):
        self.faiss_store = FaissStore(
            dimension=embedding_service.dimension,
            index_path=settings.FAISS_INDEX_PATH
        )

    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        query = state.get("rewritten_query", state.get("query", ""))
        config = state.get("config", {})
        top_k = config.get("top_k", 5)
        filters = config.get("filters") or {}
        overfetch_multiplier = max(int(filters.get("overfetch_multiplier") or 2), 1)
        min_vector_score = filters.get("min_vector_score")

        if not query:
            state["retrieved_candidates"] = []
            return state, TraceEvent(
                agent=self.name,
                action="retrieve",
                result="No query provided."
            )

        try:
            query_embedding = embedding_service.embed_one(query)
            results = self.faiss_store.search(query_embedding, top_k=top_k * overfetch_multiplier)
            if min_vector_score is not None:
                results = [
                    result for result in results
                    if result.get("score", 0) >= float(min_vector_score)
                ]
            state["retrieved_candidates"] = results
            logger.info(f"Retrieved {len(results)} candidates for query: {query}")
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            state["retrieved_candidates"] = []

        return state, TraceEvent(
            agent=self.name,
            action="retrieve",
            result=f"Found {len(state['retrieved_candidates'])} candidates."
        )
