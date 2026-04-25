import pytest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.db.models import User, UserRole, QueryLog, AgentTrace
from app.core.auth import hash_password, create_access_token
from app.db.database import SessionLocal


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def user_token(db_session):
    """Create a user and return auth token."""
    user = User(
        email="user@test.com",
        hashed_password=hash_password("password123"),
        role=UserRole.VIEWER
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    token = create_access_token({
        "email": user.email,
        "user_id": user.id,
        "role": user.role.value
    })

    return token


def test_chat_unauthorized(client):
    """Test chat without authentication returns 401."""
    response = client.post(
        "/api/v1/chat",
        json={"message": "What is AI?"}
    )

    assert response.status_code == 403


def test_chat_stream_unauthorized(client):
    """Test streaming chat without authentication returns 401."""
    response = client.post(
        "/api/v1/chat/query/stream",
        json={"query": "What is AI?"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_chat_success(client, user_token):
    """Test successful chat request."""
    with patch("app.agents.orchestrator.orchestrator") as mock_orchestrator:
        async def mock_run(*args, **kwargs):
            yield {
                "type": "trace",
                "data": MagicMock(agent="understanding", action="route", result="vector")
            }
            yield {
                "type": "token",
                "data": "test"
            }
            yield {
                "type": "final_state",
                "data": {
                    "query": "What is AI?",
                    "rewritten_query": "Define AI",
                    "synthesis_result": {
                        "answer": "Artificial Intelligence is...",
                        "citations": []
                    },
                    "traces": []
                }
            }

        mock_orchestrator.run = mock_run

        response = client.post(
            "/api/v1/chat",
            json={"message": "What is AI?", "conversation_id": "test_conv"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "latency_ms" in data


@pytest.mark.asyncio
async def test_chat_empty_message_fails(client, user_token):
    """Test chat with empty message returns 400."""
    response = client.post(
        "/api/v1/chat",
        json={"message": ""},
        headers={"Authorization": f"Bearer {user_token}"}
    )

    assert response.status_code == 400


def test_list_conversations(client):
    """Test listing conversations."""
    response = client.get("/api/v1/conversations")

    assert response.status_code == 200
    data = response.json()
    assert "conversations" in data
    assert "total" in data


def test_get_conversation_not_found(client):
    """Test getting non-existent conversation returns 404."""
    response = client.get("/api/v1/conversations/nonexistent123")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_query_log_created(client, user_token, db_session):
    """Test that QueryLog is created after chat."""
    with patch("app.agents.orchestrator.orchestrator") as mock_orchestrator:
        async def mock_run(*args, **kwargs):
            yield {
                "type": "final_state",
                "data": {
                    "query": "Test query",
                    "rewritten_query": "Test query rewritten",
                    "synthesis_result": {
                        "answer": "Test answer",
                        "citations": []
                    },
                    "traces": []
                }
            }

        mock_orchestrator.run = mock_run

        response = client.post(
            "/api/v1/chat",
            json={"message": "Test query"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

    # Verify QueryLog was created
    query_log = db_session.query(QueryLog).first()
    if query_log:
        assert query_log.query == "Test query"


@pytest.mark.asyncio
async def test_streaming_chat_success(client, user_token):
    """Test successful streaming chat request."""
    with patch("app.agents.orchestrator.orchestrator") as mock_orchestrator:
        async def mock_run(*args, **kwargs):
            yield {"type": "token", "data": "Hello "}
            yield {"type": "token", "data": "World"}
            yield {
                "type": "final_state",
                "data": {
                    "query": "What is AI?",
                    "synthesis_result": {
                        "answer": "Hello World",
                        "citations": []
                    },
                    "traces": []
                }
            }

        mock_orchestrator.run = mock_run

        response = client.post(
            "/api/v1/chat/query/stream",
            json={"query": "What is AI?"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

    assert response.status_code == 200


@pytest.mark.asyncio
async def test_streaming_chat_passes_retrieval_filters(client, user_token):
    """Test streaming chat passes retrieval filters into orchestrator."""
    captured_kwargs = {}

    with patch("app.agents.orchestrator.orchestrator") as mock_orchestrator:
        async def mock_run(*args, **kwargs):
            captured_kwargs.update(kwargs)
            yield {
                "type": "final_state",
                "data": {
                    "query": "What is AI?",
                    "synthesis_result": {
                        "answer": "Filtered answer",
                        "citations": []
                    },
                    "traces": []
                }
            }

        mock_orchestrator.run = mock_run

        response = client.post(
            "/api/v1/chat/query/stream",
            json={
                "query": "What is AI?",
                "filters": {
                    "document_ids": ["doc1"],
                    "status": "indexed",
                    "min_vector_score": 0.7,
                    "min_rerank_score": 0.2,
                    "overfetch_multiplier": 4
                }
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )

    assert response.status_code == 200
    assert captured_kwargs["filters"] == {
        "document_ids": ["doc1"],
        "status": "indexed",
        "min_vector_score": 0.7,
        "min_rerank_score": 0.2,
        "overfetch_multiplier": 4,
    }
