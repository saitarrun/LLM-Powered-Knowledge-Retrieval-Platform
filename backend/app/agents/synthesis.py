import asyncio
from typing import Dict, Any, Tuple, List
from app.agents.base import BaseAgent
from app.schemas.models import TraceEvent, Citation
from app.services.llm_provider import llm
from app.core.logging import logger

SYSTEM_PROMPT = "You are a synthesis agent. Use the provided evidence to answer the question concisely and accurately."

class SynthesisAgent(BaseAgent):
    name = "synthesis"

    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        query = state.get("query", "")
        chunks = state.get("reranked_chunks", [])
        queue = state.get("stream_queue")
        
        evidence_text = "\n".join([f"[ID: {c['db_chunk'].id}]\nText: {c['text']}" for c in chunks])
        prompt = f"Evidence:\n{evidence_text}\n\nQuestion:\n{query}"
        
        response_text = ""
        if queue:
            async for token in llm.generate_stream(SYSTEM_PROMPT, prompt):
                response_text += token
                await queue.put({"type": "token", "data": token})
        else:
            response_text = await llm.generate(SYSTEM_PROMPT, prompt)

        citations = [Citation(id=c['db_chunk'].id, document_name=c['metadata']['document_name'], chunk_text=c['text']) for c in chunks[:3]]
        if queue: await queue.put({"type": "citations", "data": [c.model_dump() for c in citations]})

        state["synthesis_result"] = {"answer": response_text, "citations": citations}
        return state, TraceEvent(agent=self.name, action="synthesize", result="Generated answer.")
