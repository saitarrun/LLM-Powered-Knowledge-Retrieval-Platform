import asyncio
from typing import Dict, Any, Tuple, List, AsyncGenerator
from app.agents.base import BaseAgent
from app.schemas.models import TraceEvent, Citation
from app.services.llm_provider import llm
from app.core.logging import logger

SYSTEM_PROMPT = "You are a synthesis agent. Use the provided evidence to answer the question concisely and accurately."


def _snippet(text: str, max_length: int = 300) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[:max_length - 3].rstrip()}..."


def _chunk_id(chunk: Dict[str, Any]) -> str | None:
    db_chunk = chunk.get("db_chunk")
    if db_chunk is not None and getattr(db_chunk, "id", None):
        return db_chunk.id
    metadata = chunk.get("metadata") or {}
    return metadata.get("chunk_id") or metadata.get("id")


def _citation_from_chunk(chunk: Dict[str, Any]) -> Citation:
    db_chunk = chunk.get("db_chunk")
    text = chunk.get("text") or getattr(db_chunk, "text", "") or ""
    chunk_id = _chunk_id(chunk)

    if db_chunk is None:
        return Citation(
            id=chunk_id,
            chunk_id=chunk_id,
            chunk_text=text,
            snippet=_snippet(text),
            available=False,
        )

    document = getattr(db_chunk, "document", None)
    document_id = getattr(db_chunk, "document_id", None) or getattr(document, "id", None)
    document_name = getattr(document, "filename", None) or (chunk.get("metadata") or {}).get("document_name")

    return Citation(
        id=chunk_id,
        chunk_id=chunk_id,
        document_id=document_id,
        document_name=document_name or "Source unavailable",
        chunk_text=text,
        snippet=_snippet(text),
        available=bool(document_id and chunk_id),
    )


def _evidence_id(chunk: Dict[str, Any], index: int) -> str:
    return _chunk_id(chunk) or f"source-{index + 1}"

class SynthesisAgent(BaseAgent):
    name = "synthesis"

    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        query = state.get("query", "")
        chunks = state.get("reranked_chunks", [])

        if not chunks:
            state["synthesis_result"] = {"answer": "", "citations": []}
            return state, TraceEvent(agent=self.name, action="synthesize", result="No chunks to synthesize.")

        evidence_text = "\n".join([
            f"[ID: {_evidence_id(c, i)}]\nText: {c.get('text', '')}"
            for i, c in enumerate(chunks)
        ])
        prompt = f"Evidence:\n{evidence_text}\n\nQuestion:\n{query}"

        response_text = await llm.generate(SYSTEM_PROMPT, prompt)
        citations = [_citation_from_chunk(c) for c in chunks[:3]]

        state["synthesis_result"] = {"answer": response_text, "citations": citations}
        return state, TraceEvent(agent=self.name, action="synthesize", result="Generated answer.")

    async def execute_stream(self, state: Dict[str, Any]) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream tokens from synthesis, yielding token, citations, and done events."""
        query = state.get("query", "")
        chunks = state.get("reranked_chunks", [])

        if not chunks:
            state["synthesis_result"] = {"answer": "", "citations": []}
            yield {"type": "done", "data": state["synthesis_result"]}
            return

        evidence_text = "\n".join([
            f"[ID: {_evidence_id(c, i)}]\nText: {c.get('text', '')}"
            for i, c in enumerate(chunks)
        ])
        prompt = f"Evidence:\n{evidence_text}\n\nQuestion:\n{query}"

        response_text = ""
        async for token in llm.generate_stream(SYSTEM_PROMPT, prompt):
            response_text += token
            yield {"type": "token", "data": token}

        citations = [_citation_from_chunk(c) for c in chunks[:3]]
        yield {"type": "citations", "data": [c.model_dump() for c in citations]}

        state["synthesis_result"] = {"answer": response_text, "citations": [c.model_dump() for c in citations]}
        yield {"type": "done", "data": state["synthesis_result"]}
