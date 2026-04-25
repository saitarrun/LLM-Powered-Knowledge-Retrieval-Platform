import json
import asyncio
from typing import Dict, Any, List
from app.agents.query_understanding import QueryUnderstandingAgent
from app.agents.retrieval import RetrievalAgent
from app.agents.evidence import EvidenceAgent
from app.agents.synthesis import SynthesisAgent
from app.agents.critic import CriticAgent
from app.agents.web_search import WebSearchAgent
from app.agents.sql_analyst import SQLAnalystAgent
from app.schemas.models import TraceEvent
from app.core.logging import logger

class Orchestrator:
    def __init__(self):
        self.understanding = QueryUnderstandingAgent()
        self.retrieval = RetrievalAgent()
        self.evidence = EvidenceAgent()
        self.synthesis = SynthesisAgent()
        self.critic = CriticAgent()
        self.web_search = WebSearchAgent()
        self.sql_analyst = SQLAnalystAgent()

    async def run(self, query: str, top_k: int = 5, session_id: str = "default", db=None, filters=None):
        state = {
            "query": query,
            "session_id": session_id,
            "config": {"top_k": top_k, "filters": filters or {}},
            "traces": [],
            "retrieved_candidates": [],
            "reranked_chunks": [],
            "synthesis_result": {},
            "validation": {},
            "db": db
        }
        
        start_time = asyncio.get_event_loop().time()
        
        # 1. Understanding & Routing
        state, trace = await self.understanding.execute(state)
        state["traces"].append(trace)
        yield {"type": "trace", "data": trace}
        
        decision = state.get("router_decision", "vector")
        
        # 2. Retrieval Branching
        if decision == "web":
            state, trace = await self.web_search.execute(state)
            state["traces"].append(trace)
            yield {"type": "trace", "data": trace}
        elif decision == "sql":
            state, trace = await self.sql_analyst.execute(state)
            state["traces"].append(trace)
            yield {"type": "trace", "data": trace}
        else:
            state, trace = await self.retrieval.execute(state)
            state["traces"].append(trace)
            yield {"type": "trace", "data": trace}

        # 3. Reranking (Evidence)
        state, trace = await self.evidence.execute(state)
        state["traces"].append(trace)
        yield {"type": "trace", "data": trace}

        # 4. Synthesis (Answer Generation)
        # We wrap synthesis in a generator for streaming
        async for msg in self.synthesis.execute_stream(state):
            if msg["type"] == "citations":
                yield msg
            elif msg["type"] == "token":
                yield msg
            elif msg["type"] == "done":
                state["synthesis_result"] = msg["data"]

        # 5. Validation (Critic)
        state, trace = await self.critic.execute(state)
        state["traces"].append(trace)
        yield {"type": "trace", "data": trace}
        
        end_time = asyncio.get_event_loop().time()
        state["latency_ms"] = int((end_time - start_time) * 1000)
        
        yield {"type": "final_state", "data": state}

orchestrator = Orchestrator()
