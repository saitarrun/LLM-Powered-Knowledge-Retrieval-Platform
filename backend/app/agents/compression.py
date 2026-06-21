from __future__ import annotations

import asyncio
from typing import Any

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState
from app.services.llm_provider import llm

SYSTEM_PROMPT = """\
You are a Context Compression Agent.
Your task is to extract ONLY the sentences, facts, or data points from the provided document that are highly relevant to answering the user's query.
If the entire text is irrelevant to the query, return the exact string: "EMPTY".
Do not add any new information, reasoning, or filler words. Extract verbatim or summarize strictly based on the text.
Return ONLY the compressed text.
"""

class ContextCompressionAgent(BaseAgent):
    name = "compression"

    async def _compress_chunk(self, query: str, chunk: dict[str, Any]) -> dict[str, Any]:
        text = chunk.get("text", "")
        if not text:
            return chunk

        prompt = f"Query: {query}\n\nDocument Text:\n{text}"
        try:
            compressed_text = await llm.generate(SYSTEM_PROMPT, prompt, temperature=0.0, max_tokens=300)
            compressed_text = compressed_text.strip()
            
            if compressed_text and compressed_text.upper() != "EMPTY":
                chunk["text"] = compressed_text
            # If LLM says EMPTY or fails, keep original text — don't discard
        except Exception as e:
            logger.error(f"Compression failed for chunk: {e}")
        
        return chunk

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        query = state.rewritten_query or state.query
        chunks = state.reranked_chunks

        if not chunks:
            return state, TraceEvent(agent=self.name, action="compress", result="No chunks to compress.")

        tasks = [self._compress_chunk(query, c) for c in chunks]
        compressed_chunks = await asyncio.gather(*tasks)

        final_chunks = [c for c in compressed_chunks if c.get("text")]
        
        original_count = len(chunks)
        final_count = len(final_chunks)
        
        state.reranked_chunks = final_chunks

        trace = TraceEvent(
            agent=self.name,
            action="compress",
            result=f"Compressed {original_count} chunks to {final_count} high-signal chunks.",
        )

        return state, trace

compression_agent = ContextCompressionAgent()
