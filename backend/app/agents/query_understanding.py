from __future__ import annotations

import json

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState
from app.services.llm_provider import llm

SYSTEM_PROMPT = """You are a Query Understanding Agent.
Analyze the user query and decide the best routing strategy.
Options:
- "vector": Standard semantic search (default)
- "sql": Database analytics (if query asks about document stats, counts, or structured data)
- "web": If query asks for real-time information or mentions 'online'

Also generate 3 distinct query variations that rephrase the intent differently to maximize retrieval recall.
Each variation should use different vocabulary or framing.
Crucially, generate a "hypothetical_document": a short, 2-3 sentence confident (but fake) answer to the user's query. This will be used for HyDE (Hypothetical Document Embeddings) to bridge the vocabulary gap in vector search.

Return ONLY VALID JSON in this exact shape:
{
  "router_decision": "vector",
  "intent": "qa",
  "rewritten_query": "primary rewritten query",
  "query_variations": ["variation 1", "variation 2", "variation 3"],
  "hypothetical_document": "Fake answer here..."
}
Do not include markdown blocks.
"""


class QueryUnderstandingAgent(BaseAgent):
    name = "query_understanding"

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        original_query = state.query
        logger.info(f"Query Understanding: {original_query}")

        response = await llm.generate(SYSTEM_PROMPT, f"Query: {original_query}", temperature=0.0)

        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned)
            rewritten_query = result.get("rewritten_query", original_query)
            intent = result.get("intent", "qa")
            router_decision = result.get("router_decision", "vector")
            query_variations = result.get("query_variations") or []
            hyde_doc = result.get("hypothetical_document")
            if hyde_doc:
                query_variations.append(hyde_doc)
            if rewritten_query not in query_variations:
                query_variations = [rewritten_query] + query_variations
        except Exception as e:
            logger.error(f"Failed to parse router decision: {e} - Raw: {response}")
            rewritten_query = original_query
            intent = "qa"
            router_decision = "vector"
            query_variations = [original_query]

        state.rewritten_query = rewritten_query
        state.query_variations = query_variations
        state.intent = intent
        state.router_decision = router_decision

        trace = TraceEvent(
            agent=self.name,
            action="route_and_rewrite",
            result=f"Routed -> {router_decision.upper()} | Intent: {intent} | Variations: {len(query_variations)}",
        )

        return state, trace
