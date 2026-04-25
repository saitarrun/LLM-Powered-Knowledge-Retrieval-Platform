from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.agents.synthesis import SynthesisAgent


def make_chunk(chunk_id="chunk1", document_id="doc1", filename="source.pdf", text="This is source text."):
    document = SimpleNamespace(id=document_id, filename=filename)
    db_chunk = SimpleNamespace(id=chunk_id, document_id=document_id, document=document, text=text)
    return {
        "text": text,
        "metadata": {"chunk_id": chunk_id},
        "db_chunk": db_chunk,
    }


@pytest.mark.asyncio
async def test_synthesis_serializes_citation_source_fields():
    agent = SynthesisAgent()
    state = {"query": "What is sourced?", "reranked_chunks": [make_chunk()]}

    with patch("app.agents.synthesis.llm.generate", new=AsyncMock(return_value="Answer.")):
        result_state, trace = await agent.execute(state)

    citation = result_state["synthesis_result"]["citations"][0].model_dump()
    assert citation["document_name"] == "source.pdf"
    assert citation["document_id"] == "doc1"
    assert citation["chunk_id"] == "chunk1"
    assert citation["chunk_text"] == "This is source text."
    assert citation["snippet"] == "This is source text."
    assert citation["available"] is True


@pytest.mark.asyncio
async def test_synthesis_serializes_unavailable_citation_when_chunk_reference_missing():
    agent = SynthesisAgent()
    state = {
        "query": "What is sourced?",
        "reranked_chunks": [
            {
                "text": "Fallback source text.",
                "metadata": {"chunk_id": "missing-chunk"},
                "db_chunk": None,
            }
        ],
    }

    with patch("app.agents.synthesis.llm.generate", new=AsyncMock(return_value="Answer.")):
        result_state, trace = await agent.execute(state)

    citation = result_state["synthesis_result"]["citations"][0].model_dump()
    assert citation["document_name"] == "Source unavailable"
    assert citation["document_id"] is None
    assert citation["chunk_id"] == "missing-chunk"
    assert citation["snippet"] == "Fallback source text."
    assert citation["available"] is False
