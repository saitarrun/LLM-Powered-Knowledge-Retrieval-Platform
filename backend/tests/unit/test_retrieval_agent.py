from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.agents.retrieval import RetrievalAgent
from app.schemas.query_state import QueryState, RetrievalConfig
from unittest.mock import patch

@pytest.fixture(autouse=True)
def mock_graph_extractor():
    with patch("app.agents.retrieval.graph_extractor") as mock_extractor:
        mock_extractor.query_graph = AsyncMock(return_value=["Graph Context 1"])
        yield mock_extractor


def make_agent(search_results=None):
    mock_store = MagicMock()
    default = [
        {"score": 0.95, "metadata": {"chunk_id": "chunk1"}},
        {"score": 0.85, "metadata": {"chunk_id": "chunk2"}},
    ]
    mock_store.search_multi = AsyncMock(
        return_value=search_results if search_results is not None else default
    )
    return RetrievalAgent(store=mock_store), mock_store


@pytest.mark.asyncio
async def test_retrieval_agent_execute():
    agent, _ = make_agent()
    state = QueryState(query="What is machine learning?", rewritten_query="Define machine learning")

    result_state, trace = await agent.execute(state)

    assert trace.agent == "retrieval"
    assert len(result_state.retrieved_candidates) > 0


@pytest.mark.asyncio
async def test_retrieval_agent_empty_results():
    agent, _ = make_agent(search_results=[])
    state = QueryState(query="xyzabc nonexistent term", rewritten_query="xyzabc nonexistent term")

    result_state, trace = await agent.execute(state)

    assert trace.agent == "retrieval"
    assert len(result_state.retrieved_candidates) == 1
    assert result_state.retrieved_candidates[0]["metadata"]["chunk_id"] == "graph_node"


@pytest.mark.asyncio
async def test_retrieval_agent_top_k():
    results = [
        {"score": 0.9 - (i * 0.05), "metadata": {"chunk_id": f"chunk{i}"}} for i in range(10)
    ]
    agent, mock_store = make_agent(search_results=results)
    state = QueryState(query="test query", config=RetrievalConfig(top_k=10))

    await agent.execute(state)

    mock_store.search_multi.assert_called_once()
    _, kwargs = mock_store.search_multi.call_args
    assert kwargs.get("top_k") == 20


@pytest.mark.asyncio
async def test_retrieval_agent_overfetch_multiplier():
    agent, mock_store = make_agent()
    state = QueryState(
        query="test query",
        config=RetrievalConfig(top_k=5, filters={"overfetch_multiplier": 4}),
    )

    await agent.execute(state)

    _, kwargs = mock_store.search_multi.call_args
    assert kwargs.get("top_k") == 20


@pytest.mark.asyncio
async def test_retrieval_agent_uses_query_variations():
    agent, mock_store = make_agent()
    variations = ["Define ML", "What is machine learning", "ML definition"]
    state = QueryState(
        query="What is ML?",
        rewritten_query="Define ML",
        query_variations=variations,
    )

    await agent.execute(state)

    args, _ = mock_store.search_multi.call_args
    assert args[0] == variations
