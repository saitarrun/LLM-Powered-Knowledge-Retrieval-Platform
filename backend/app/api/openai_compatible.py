from fastapi import APIRouter, Request

from app.services.openai_compatible_adapter import forward_chat_completion

router = APIRouter(tags=["openai-compatible"])


@router.post("/chat/completions")
async def chat_completions(request: Request):
    body = await request.json()
    authorization = request.headers.get("Authorization")
    return await forward_chat_completion(body, authorization)
