from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_chat_completions_forwards_to_provider(client, monkeypatch):
    monkeypatch.setattr(settings, "LLM_BASE_URL", "http://fake-provider.local")

    provider_response = {
        "id": "chatcmpl-test",
        "object": "chat.completion",
        "created": 1234567890,
        "model": "llama3.2",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello!"},
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 5,
            "total_tokens": 15,
        },
    }

    mock_http_response = MagicMock()
    mock_http_response.is_error = False
    mock_http_response.status_code = 200
    mock_http_response.json.return_value = provider_response

    mock_http_client = AsyncMock()
    mock_http_client.post = AsyncMock(return_value=mock_http_response)
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=None)

    with patch(
        "app.services.openai_compatible_adapter.httpx.AsyncClient",
        return_value=mock_http_client,
    ):
        response = client.post(
            "/v1/chat/completions",
            json={
                "model": "llama3.2",
                "messages": [{"role": "user", "content": "hello"}],
                "stream": False,
            },
        )

    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert data["choices"][0]["message"]["content"] == "Hello!"
    assert "usage" in data

    mock_http_client.post.assert_called_once()
    call_kwargs = mock_http_client.post.call_args.kwargs
    assert (
        mock_http_client.post.call_args.args[0] == "http://fake-provider.local/v1/chat/completions"
    )
    assert call_kwargs["json"] == {
        "model": "llama3.2",
        "messages": [{"role": "user", "content": "hello"}],
        "stream": False,
    }
    assert "headers" not in call_kwargs or "Authorization" not in call_kwargs.get("headers", {})
