from typing import Any

import httpx
from fastapi import HTTPException

from app.core.config import settings


async def forward_chat_completion(
    body: dict[str, Any],
    authorization: str | None = None,
) -> dict[str, Any]:
    url = f"{settings.LLM_BASE_URL.rstrip('/')}/v1/chat/completions"
    headers: dict[str, str] = {}
    if authorization:
        headers["Authorization"] = authorization

    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=body, headers=headers, timeout=60.0)

    if response.is_error:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text or response.reason_phrase
        raise HTTPException(status_code=response.status_code, detail=detail)

    return response.json()
