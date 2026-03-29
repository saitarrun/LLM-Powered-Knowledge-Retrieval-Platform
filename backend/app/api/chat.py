"""Chat and conversation routes."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(tags=["chat"])

class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None

@router.post("/chat")
async def chat(request: ChatMessage):
    """Send a message and get a response."""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")
        
        return {
            "conversation_id": request.conversation_id or "new",
            "message": request.message,
            "response": "I'm ready to help with your knowledge retrieval queries.",
            "sources": []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/conversations")
async def list_conversations():
    """List all conversations."""
    return {
        "conversations": [],
        "total": 0
    }

@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation details."""
    return {
        "id": conversation_id,
        "messages": [],
        "created_at": "2026-03-29T00:00:00Z"
    }
