from __future__ import annotations

"""Chat and conversation routes with streaming support."""

import json
import time
from collections.abc import AsyncGenerator
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.agents import orchestrator as orchestrator_module
import asyncio
from app.core.logging import logger
from app.core.permissions import TokenData, require_role
from app.db.database import get_db
from app.db.models import QueryLog
from app.db.repositories import query_log_repository
from app.services.embedding import embedding_service
from app.services.semantic_cache import semantic_cache

router = APIRouter(tags=["chat"])


class RetrievalFilters(BaseModel):
    document_ids: list[str] | None = None
    filename_contains: str | None = None
    status: str | None = None
    approval_required: bool | None = None
    approved_by: str | None = None
    created_after: datetime | None = None
    created_before: datetime | None = None
    min_vector_score: float | None = None
    min_rerank_score: float | None = None
    overfetch_multiplier: int | None = None


class ChatRequest(BaseModel):
    query: str
    conversation_id: str | None = None
    top_k: int = 5
    filters: RetrievalFilters | None = None


class ChatMessage(BaseModel):
    message: str
    conversation_id: str | None = None
    top_k: int = 5
    filters: RetrievalFilters | None = None


@router.post("/chat")
async def chat(
    request: ChatMessage,
    current_user: TokenData = Depends(require_role(["viewer", "curator", "admin"])),
    db: Session = Depends(get_db),
):
    """Send a message and get a response (non-streaming, for backwards compatibility)."""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        start_time = time.time()
        
        query_vector = await asyncio.to_thread(embedding_service.embed_one, request.message)
        cached_result = await asyncio.to_thread(semantic_cache.get, query_vector)
        
        if cached_result:
            latency_ms = int((time.time() - start_time) * 1000)
            cached_result["latency_ms"] = latency_ms
            cached_result["cached"] = True
            return cached_result

        # Call orchestrator
        final_state = {}
        async for event in orchestrator_module.orchestrator.run(
            query=request.message,
            top_k=request.top_k,
            session_id=request.conversation_id or "default",
            db=db,
            filters=request.filters.model_dump(exclude_none=True) if request.filters else None,
        ):
            if event["type"] == "final_state":
                final_state = event["data"]

        # Extract answer and citations
        answer = final_state.synthesis_result.get("answer", "") if final_state else ""
        citations = final_state.synthesis_result.get("citations", []) if final_state else []
        latency_ms = int((time.time() - start_time) * 1000)

        if final_state:
            query_log_repository.persist(
                db=db,
                state=final_state,
                user_id=current_user.user_id,
                conversation_id=request.conversation_id,
                latency_ms=latency_ms,
            )

        result_payload = {
            "conversation_id": request.conversation_id or "new",
            "message": request.message,
            "response": answer,
            "citations": citations if isinstance(citations, list) else [],
            "validation": final_state.validation if final_state else {},
            "latency_ms": latency_ms,
        }
        
        # Save to semantic cache
        if answer:
            await asyncio.to_thread(semantic_cache.set, query_vector, request.message, result_payload)
            
        return result_payload

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/chat/query/stream")
async def chat_query_stream(
    request: ChatRequest,
    current_user: TokenData = Depends(require_role(["viewer", "curator", "admin"])),
    db: Session = Depends(get_db),
):
    """Stream orchestrator output as Server-Sent Events (SSE)."""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            start_time = time.time()
            
            query_vector = await asyncio.to_thread(embedding_service.embed_one, request.query)
            cached_result = await asyncio.to_thread(semantic_cache.get, query_vector)
            
            if cached_result:
                # Replay cached result as stream events
                yield f"data: {json.dumps({'type': 'trace', 'agent': 'cache', 'action': 'semantic_hit', 'result': 'Found in cache'})}\n\n"
                
                # yield tokens
                for token in cached_result.get("response", "").split():
                    yield f"data: {json.dumps({'type': 'token', 'token': token + ' '})}\n\n"
                    
                if cached_result.get("citations"):
                    yield f"data: {json.dumps({'type': 'citations', 'citations': cached_result['citations']})}\n\n"
                if cached_result.get("validation"):
                    yield f"data: {json.dumps({'type': 'validation', 'validation': cached_result['validation']})}\n\n"
                    
                yield f"data: {json.dumps({'type': 'done'})}\n\n"
                return

            final_state = {}

            async for event in orchestrator_module.orchestrator.run(
                query=request.query,
                top_k=request.top_k,
                session_id=request.conversation_id or "default",
                db=db,
                filters=request.filters.model_dump(exclude_none=True) if request.filters else None,
            ):
                if event["type"] == "trace":
                    trace_data = event["data"]
                    yield f"data: {json.dumps({'type': 'trace', 'agent': trace_data.agent, 'action': trace_data.action, 'result': trace_data.result})}\n\n"

                elif event["type"] == "token":
                    yield f"data: {json.dumps({'type': 'token', 'token': event['data']})}\n\n"

                elif event["type"] == "citations":
                    yield f"data: {json.dumps({'type': 'citations', 'citations': event['data']})}\n\n"

                elif event["type"] == "final_state":
                    final_state = event["data"]

            latency_ms = int((time.time() - start_time) * 1000)
            if final_state:
                query_log_repository.persist(
                    db=db,
                    state=final_state,
                    user_id=current_user.user_id,
                    conversation_id=request.conversation_id,
                    latency_ms=latency_ms,
                )
                yield f"data: {json.dumps({'type': 'validation', 'validation': final_state.validation})}\n\n"
                
                # Save to semantic cache
                result_payload = {
                    "conversation_id": request.conversation_id or "new",
                    "message": request.query,
                    "response": final_state.synthesis_result.get("answer", ""),
                    "citations": final_state.synthesis_result.get("citations", []),
                    "validation": final_state.validation,
                    "latency_ms": latency_ms,
                }
                await asyncio.to_thread(semantic_cache.set, query_vector, request.query, result_payload)

            logger.info(f"Query completed in {latency_ms}ms")

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/conversations")
async def list_conversations(db: Session = Depends(get_db)):
    """List all conversations."""
    try:
        # Group query logs by conversation_id
        logs = db.query(QueryLog).all()

        conversations = {}
        for log in logs:
            conv_id = log.conversation_id or "default"
            if conv_id not in conversations:
                conversations[conv_id] = {
                    "id": conv_id,
                    "query_count": 0,
                    "created_at": log.created_at.isoformat(),
                    "last_query_at": log.created_at.isoformat(),
                }
            conversations[conv_id]["query_count"] += 1
            conversations[conv_id]["last_query_at"] = log.created_at.isoformat()

        return {"conversations": list(conversations.values()), "total": len(conversations)}

    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation messages and details."""
    try:
        logs = (
            db.query(QueryLog)
            .filter(QueryLog.conversation_id == conversation_id)
            .order_by(QueryLog.created_at)
            .all()
        )

        if not logs:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = []
        for log in logs:
            messages.append(
                {"role": "user", "content": log.query, "timestamp": log.created_at.isoformat()}
            )
            messages.append(
                {
                    "role": "assistant",
                    "content": log.answer,
                    "latency_ms": log.latency_ms,
                    "timestamp": log.created_at.isoformat(),
                }
            )

        return {
            "id": conversation_id,
            "messages": messages,
            "created_at": logs[0].created_at.isoformat() if logs else None,
            "updated_at": logs[-1].created_at.isoformat() if logs else None,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e
