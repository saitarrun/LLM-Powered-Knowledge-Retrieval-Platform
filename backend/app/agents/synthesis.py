from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Any

from app.agents.base import BaseAgent
from app.schemas.models import Citation, TraceEvent
from app.schemas.query_state import QueryState
from app.services.llm_provider import llm

SYSTEM_PROMPT = """\
You are a synthesis agent that answers questions strictly from the provided sources.

Rules:
- Cite sources inline using [N] notation — e.g. "The model achieves 94% accuracy [1]."
- Use only information present in the provided sources. Do not add facts from outside knowledge.
- If the sources do not contain enough information to fully answer, say so explicitly.
- If sources contradict each other, note the disagreement and cite both sides.
- Be concise and direct. Avoid filler phrases like "Based on the provided context...".\
"""


def _snippet(text: str, max_length: int = 300) -> str:
    if not text:
        return ""
    normalized = " ".join(text.split())
    if len(normalized) <= max_length:
        return normalized
    return f"{normalized[: max_length - 3].rstrip()}..."


def _chunk_id(chunk: dict[str, Any]) -> str | None:
    db_chunk = chunk.get("db_chunk")
    if db_chunk is not None and getattr(db_chunk, "id", None):
        return db_chunk.id
    metadata = chunk.get("metadata") or {}
    return metadata.get("chunk_id") or metadata.get("id")


def _citation_from_chunk(chunk: dict[str, Any]) -> Citation:
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
    document_name = getattr(document, "filename", None) or (chunk.get("metadata") or {}).get(
        "document_name"
    )

    return Citation(
        id=chunk_id,
        chunk_id=chunk_id,
        document_id=document_id,
        document_name=document_name or "Source unavailable",
        chunk_text=text,
        snippet=_snippet(text),
        available=bool(document_id and chunk_id),
    )


def _format_source(chunk: dict[str, Any], index: int) -> str:
    """Render one chunk as a numbered source block for the LLM prompt."""
    db_chunk = chunk.get("db_chunk")
    doc_name = None
    page = None
    if db_chunk is not None:
        doc = getattr(db_chunk, "document", None)
        doc_name = getattr(doc, "filename", None)
        page = getattr(db_chunk, "page_number", None)

    header = f"[{index + 1}]"
    if doc_name:
        header += f" {doc_name}"
    if page is not None:
        header += f", p.{page}"

    # Use parent_text if available for hierarchical chunking context
    chunk_text = getattr(db_chunk, "parent_text", None) if db_chunk else None
    if not chunk_text:
        chunk_text = chunk.get("text", getattr(db_chunk, "text", ""))

    return f"{header}\n{chunk_text}"


def _build_prompt(query: str, chunks: list[dict[str, Any]]) -> str:
    sources = "\n\n".join(_format_source(c, i) for i, c in enumerate(chunks))
    return f"Sources:\n{sources}\n\nQuestion: {query}"


class SynthesisAgent(BaseAgent):
    name = "synthesis"

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        query = state.rewritten_query or state.query
        chunks = state.reranked_chunks

        if not chunks:
            state.synthesis_result = {"answer": "", "citations": []}
            return state, TraceEvent(
                agent=self.name, action="synthesize", result="No chunks to synthesize."
            )

        prompt = _build_prompt(query, chunks)
        response_text = await llm.generate(SYSTEM_PROMPT, prompt)
        citations = [_citation_from_chunk(c) for c in chunks]

        state.synthesis_result = {"answer": response_text, "citations": citations}
        return state, TraceEvent(agent=self.name, action="synthesize", result="Generated answer.")

    async def execute_stream(self, state: QueryState) -> AsyncGenerator[dict[str, Any], None]:
        """Stream tokens from synthesis, yielding token, citations, and done events."""
        query = state.rewritten_query or state.query
        chunks = state.reranked_chunks

        if not chunks:
            state.synthesis_result = {"answer": "", "citations": []}
            yield {"type": "done", "data": state.synthesis_result}
            return

        prompt = _build_prompt(query, chunks)

        response_text = ""
        async for token in llm.generate_stream(SYSTEM_PROMPT, prompt):
            response_text += token
            yield {"type": "token", "data": token}

        citations = [_citation_from_chunk(c) for c in chunks]
        yield {"type": "citations", "data": [c.model_dump() for c in citations]}

        state.synthesis_result = {
            "answer": response_text,
            "citations": [c.model_dump() for c in citations],
        }
        yield {"type": "done", "data": state.synthesis_result}
