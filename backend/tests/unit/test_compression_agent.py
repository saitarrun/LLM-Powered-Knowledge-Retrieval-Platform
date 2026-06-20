from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.compression import ContextCompressionAgent
from app.schemas.query_state import QueryState

@pytest.fixture(autouse=True)
def mock_llm_generate():
    with patch("app.agents.compression.llm.generate", new_callable=AsyncMock) as mock_gen:
        yield mock_gen

@pytest.mark.asyncio
async def test_compression_agent_extracts_text(mock_llm_generate):
    mock_llm_generate.return_value = "This is the highly relevant extracted text."
    
    agent = ContextCompressionAgent()
    state = QueryState(
        query="What is AI?",
        reranked_chunks=[{"metadata": {"chunk_id": "chunk1"}, "text": "Original long text full of fluff..."}],
    )

    result_state, trace = await agent.execute(state)

    assert trace.agent == "compression"
    assert "Compressed" in trace.result
    
    assert len(result_state.reranked_chunks) == 1
    assert result_state.reranked_chunks[0]["text"] == "This is the highly relevant extracted text."

@pytest.mark.asyncio
async def test_compression_agent_filters_empty(mock_llm_generate):
    mock_llm_generate.return_value = "EMPTY"
    
    agent = ContextCompressionAgent()
    state = QueryState(
        query="What is AI?",
        reranked_chunks=[{"metadata": {"chunk_id": "chunk1"}, "text": "Original long text full of fluff..."}],
    )

    result_state, trace = await agent.execute(state)

    assert trace.agent == "compression"
    assert len(result_state.reranked_chunks) == 0

@pytest.mark.asyncio
async def test_compression_agent_no_chunks(mock_llm_generate):
    agent = ContextCompressionAgent()
    state = QueryState(
        query="What is AI?",
        reranked_chunks=[],
    )

    result_state, trace = await agent.execute(state)

    assert trace.agent == "compression"
    assert trace.result == "No chunks to compress."
    assert len(result_state.reranked_chunks) == 0
