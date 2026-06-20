from __future__ import annotations

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState


class WebSearchAgent(BaseAgent):
    name = "web_search"

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        query = state.rewritten_query or state.query
        logger.info(f"Web Search Agent searching for: {query}")

        search_result = (
            f"Real-time search results for '{query}': The Nexus Platform is currently operating "
            "in 'Core Mode'. Web search integration is pending API key configuration for Tavily/SerpAPI."
        )

        state.retrieved_candidates.append(
            {
                "score": 0.9,
                "metadata": {"document_name": "Web Intelligence", "chunk_id": "web-0", "page": 1},
                "text": search_result,
            }
        )

        return state, TraceEvent(
            agent=self.name,
            action="web_search",
            result=f"Simulated search for '{query[:30]}...'",
        )
