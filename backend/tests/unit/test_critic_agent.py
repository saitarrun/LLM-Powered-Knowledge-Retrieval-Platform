from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from app.agents.critic import CriticAgent
from app.schemas.query_state import QueryState


@pytest.fixture(autouse=True)
def mock_llm_generate():
    with patch("app.agents.critic.llm.generate", new_callable=AsyncMock) as mock_gen:
        # We need a side effect or fixed return value for generate.
        # But for tests, we can just let it return the string we want based on the test.
        yield mock_gen

@pytest.mark.asyncio
async def test_critic_agent_high_confidence_with_citations(mock_llm_generate):
    mock_llm_generate.return_value = '{"confidence": "high", "note": "The answer is completely grounded."}'
    agent = CriticAgent()
    state = QueryState(
        query="What is AI?",
        synthesis_result={
            "answer": "Artificial Intelligence is...",
            "citations": [{"chunk_id": "chunk1", "text": "AI definition...", "score": 0.9}],
        },
        reranked_chunks=[{"metadata": {"chunk_id": "chunk1"}, "text": "AI definition..."}],
    )

    result_state, trace = await agent.execute(state)

    assert trace.agent == "critic"
    assert trace.action == "validate"
    assert "grounded" in trace.result.lower() or "source" in trace.result.lower()

@pytest.mark.asyncio
async def test_critic_agent_low_confidence_no_citations(mock_llm_generate):
    mock_llm_generate.return_value = '{"confidence": "low", "note": "The answer is not supported by the sources."}'
    agent = CriticAgent()
    state = QueryState(
        query="What is AI?",
        synthesis_result={"answer": "Artificial Intelligence is...", "citations": []},
        reranked_chunks=[{"metadata": {"chunk_id": "chunk1"}, "text": "AI definition..."}],
    )

    result_state, trace = await agent.execute(state)

    assert trace.agent == "critic"
    assert "low" in trace.result.lower() or "supported" in trace.result.lower()

@pytest.mark.asyncio
async def test_critic_agent_low_confidence_empty_answer():
    agent = CriticAgent()
    state = QueryState(
        query="What is AI?",
        synthesis_result={"answer": "", "citations": []},
        reranked_chunks=[],
    )

    result_state, trace = await agent.execute(state)

    assert trace.agent == "critic"
    assert result_state.validation["confidence"] == "low"
    assert "empty" in trace.result.lower() or "no answer" in trace.result.lower()

@pytest.mark.asyncio
async def test_critic_agent_populates_validation(mock_llm_generate):
    mock_llm_generate.return_value = '{"confidence": "high", "note": "The answer is perfectly grounded."}'
    agent = CriticAgent()
    state = QueryState(
        query="Test query",
        synthesis_result={"answer": "Test answer", "citations": [{"chunk_id": "chunk1"}]},
        reranked_chunks=[{"metadata": {"chunk_id": "chunk1"}, "text": "Test answer"}],
    )

    result_state, trace = await agent.execute(state)
    assert result_state.validation["confidence"] == "high"

    assert result_state.validation["confidence"] == "high"
    assert result_state.query == "Test query"
    assert result_state.synthesis_result["answer"] == "Test answer"
