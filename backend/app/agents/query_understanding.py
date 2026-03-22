import json
from typing import Dict, Any, Tuple
from app.agents.base import BaseAgent
from app.schemas.models import TraceEvent
from app.services.llm_provider import llm
from app.core.logging import logger

SYSTEM_PROMPT = """You are a Query Understanding Agent. 
Analyze the user query and decide the best routing strategy.
Options:
- "vector": Standard semantic search (default)
- "sql": Database analytics (if query asks about document stats, counts, or structured data)
- "web": If query asks for real-time information or mentions 'online'

Also rewrite the query for better retrieval if needed.

Return ONLY VALID JSON. Do not include markdown blocks.
"""

class QueryUnderstandingAgent(BaseAgent):
    name = "query_understanding"

    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        original_query = state.get("query", "")
        logger.info(f"Query Understanding: {original_query}")
        
        response = await llm.generate(SYSTEM_PROMPT, f"Query: {original_query}", temperature=0.0)
        
        try:
            cleaned = response.replace("```json", "").replace("```", "").strip()
            result = json.loads(cleaned)
            rewritten_query = result.get("rewritten_query", original_query)
            intent = result.get("intent", "qa")
            router_decision = result.get("router_decision", "vector")
        except Exception as e:
            logger.error(f"Failed to parse router decision: {e} - Raw: {response}")
            rewritten_query = original_query
            intent = "qa"
            router_decision = "vector"
            
        state["rewritten_query"] = rewritten_query
        state["intent"] = intent
        state["router_decision"] = router_decision
        
        trace = TraceEvent(
            agent=self.name,
            action="route_and_rewrite",
            result=f"Routed -> {router_decision.upper()} | Intent: {intent} | Rewrote: {rewritten_query}"
        )
        
        return state, trace
