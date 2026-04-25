import pytest
from app.agents.critic import CriticAgent


@pytest.mark.asyncio
async def test_critic_agent_high_confidence_with_citations():
    """Test critic agent gives high confidence when citations exist."""
    agent = CriticAgent()

    state = {
        "query": "What is AI?",
        "synthesis_result": {
            "answer": "Artificial Intelligence is...",
            "citations": [
                {"chunk_id": "chunk1", "text": "AI definition...", "score": 0.9}
            ]
        }
    }

    result_state, trace = await agent.execute(state)

    assert trace.agent == "critic"
    assert trace.action == "validate"
    assert "grounded" in trace.result.lower() or "source" in trace.result.lower()


@pytest.mark.asyncio
async def test_critic_agent_low_confidence_no_citations():
    """Test critic agent gives low confidence when no citations exist."""
    agent = CriticAgent()

    state = {
        "query": "What is AI?",
        "synthesis_result": {
            "answer": "Artificial Intelligence is...",
            "citations": []
        }
    }

    result_state, trace = await agent.execute(state)

    assert trace.agent == "critic"
    assert "low" in trace.result.lower() or "no citations" in trace.result.lower()


@pytest.mark.asyncio
async def test_critic_agent_low_confidence_empty_answer():
    """Test critic agent gives low confidence for empty answers."""
    agent = CriticAgent()

    state = {
        "query": "What is AI?",
        "synthesis_result": {
            "answer": "",
            "citations": []
        }
    }

    result_state, trace = await agent.execute(state)

    assert trace.agent == "critic"
    assert "no answer" in trace.result.lower()


@pytest.mark.asyncio
async def test_critic_agent_preserves_state():
    """Test critic agent returns modified state."""
    agent = CriticAgent()

    state = {
        "query": "Test query",
        "synthesis_result": {
            "answer": "Test answer",
            "citations": [{"chunk_id": "chunk1"}]
        },
        "validation": {}
    }

    result_state, trace = await agent.execute(state)

    assert "validation" in result_state
    assert result_state["query"] == "Test query"
    assert result_state["synthesis_result"]["answer"] == "Test answer"
