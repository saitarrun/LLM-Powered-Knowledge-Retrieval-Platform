import pytest
from unittest.mock import patch, MagicMock
from app.agents.retrieval import RetrievalAgent
from app.schemas.models import TraceEvent


def make_agent_with_mock_faiss(search_results=None):
    """Create a RetrievalAgent with a mocked FaissStore instance."""
    mock_faiss = MagicMock()
    # Use explicit None check so empty list works correctly
    mock_faiss.search.return_value = search_results if search_results is not None else [
        {"score": 0.95, "metadata": {"chunk_id": "chunk1"}},
        {"score": 0.85, "metadata": {"chunk_id": "chunk2"}},
    ]
    mock_faiss.dimension = 384

    with patch("app.agents.retrieval.FaissStore", return_value=mock_faiss):
        with patch("app.agents.retrieval.embedding_service") as mock_embed:
            mock_embed.dimension = 384
            mock_embed.embed_one.return_value = [0.1] * 384
            agent = RetrievalAgent()
            agent.faiss_store = mock_faiss

    return agent, mock_faiss


@pytest.mark.asyncio
async def test_retrieval_agent_execute():
    """Test retrieval agent executes and returns results."""
    agent, mock_faiss = make_agent_with_mock_faiss()

    state = {
        "query": "What is machine learning?",
        "rewritten_query": "Define machine learning",
        "retrieved_candidates": [],
    }

    with patch("app.agents.retrieval.embedding_service") as mock_embed:
        mock_embed.embed_one.return_value = [0.1] * 384
        result_state, trace = await agent.execute(state)

    assert trace is not None
    assert trace.agent == "retrieval"
    assert result_state["retrieved_candidates"] is not None
    assert len(result_state["retrieved_candidates"]) > 0


@pytest.mark.asyncio
async def test_retrieval_agent_empty_results():
    """Test retrieval agent handles empty results."""
    agent, mock_faiss = make_agent_with_mock_faiss(search_results=[])

    state = {
        "query": "xyzabc nonexistent term",
        "rewritten_query": "xyzabc nonexistent term",
        "retrieved_candidates": [],
    }

    with patch("app.agents.retrieval.embedding_service") as mock_embed:
        mock_embed.embed_one.return_value = [0.1] * 384
        result_state, trace = await agent.execute(state)

    assert trace.agent == "retrieval"
    assert result_state["retrieved_candidates"] == []


@pytest.mark.asyncio
async def test_retrieval_agent_top_k():
    """Test retrieval agent respects top_k parameter."""
    results = [
        {"score": 0.9 - (i * 0.05), "metadata": {"chunk_id": f"chunk{i}"}}
        for i in range(10)
    ]
    agent, mock_faiss = make_agent_with_mock_faiss(search_results=results)

    state = {
        "query": "test query",
        "rewritten_query": "test query",
        "retrieved_candidates": [],
        "config": {"top_k": 10},
    }

    with patch("app.agents.retrieval.embedding_service") as mock_embed:
        mock_embed.embed_one.return_value = [0.1] * 384
        result_state, trace = await agent.execute(state)

    # Verify search was called with top_k * 2
    mock_faiss.search.assert_called_once()
    call_args = mock_faiss.search.call_args
    # top_k * 2 = 20 per the agent's implementation
    assert call_args[1].get("top_k") == 20 or (len(call_args[0]) > 1 and call_args[0][1] == 20)


@pytest.mark.asyncio
async def test_retrieval_agent_applies_quality_filters():
    """Test retrieval applies overfetch and minimum vector score filters."""
    results = [
        {"score": 0.95, "metadata": {"chunk_id": "chunk1"}},
        {"score": 0.69, "metadata": {"chunk_id": "chunk2"}},
        {"score": 0.70, "metadata": {"chunk_id": "chunk3"}},
    ]
    agent, mock_faiss = make_agent_with_mock_faiss(search_results=results)

    state = {
        "query": "test query",
        "rewritten_query": "test query",
        "retrieved_candidates": [],
        "config": {
            "top_k": 5,
            "filters": {
                "min_vector_score": 0.7,
                "overfetch_multiplier": 4,
            },
        },
    }

    with patch("app.agents.retrieval.embedding_service") as mock_embed:
        mock_embed.embed_one.return_value = [0.1] * 384
        result_state, trace = await agent.execute(state)

    mock_faiss.search.assert_called_once()
    call_args = mock_faiss.search.call_args
    assert call_args[1].get("top_k") == 20 or (len(call_args[0]) > 1 and call_args[0][1] == 20)
    assert [c["metadata"]["chunk_id"] for c in result_state["retrieved_candidates"]] == ["chunk1", "chunk3"]
