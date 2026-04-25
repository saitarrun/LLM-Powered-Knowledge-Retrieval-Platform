"""Chat and conversation routes with streaming support."""
import json
import time
from datetime import datetime
from typing import Optional, AsyncGenerator
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import QueryLog, AgentTrace
from app.agents import orchestrator as orchestrator_module
from app.core.logging import logger
from app.core.permissions import require_role, TokenData

router = APIRouter(tags=["chat"])


class RetrievalFilters(BaseModel):
    document_ids: Optional[list[str]] = None
    filename_contains: Optional[str] = None
    status: Optional[str] = None
    approval_required: Optional[bool] = None
    approved_by: Optional[str] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    min_vector_score: Optional[float] = None
    min_rerank_score: Optional[float] = None
    overfetch_multiplier: Optional[int] = None


class ChatRequest(BaseModel):
    query: str
    conversation_id: Optional[str] = None
    top_k: int = 5
    filters: Optional[RetrievalFilters] = None


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    top_k: int = 5
    filters: Optional[RetrievalFilters] = None


@router.post("/chat")
async def chat(
    request: ChatMessage,
    current_user: TokenData = Depends(require_role(["viewer", "curator", "admin"])),
    db: Session = Depends(get_db)
):
    """Send a message and get a response (non-streaming, for backwards compatibility)."""
    try:
        if not request.message or not request.message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        start_time = time.time()

        # Call orchestrator
        final_state = {}
        async for event in orchestrator_module.orchestrator.run(
            query=request.message,
            top_k=request.top_k,
            session_id=request.conversation_id or "default",
            db=db,
            filters=request.filters.model_dump(exclude_none=True) if request.filters else None
        ):
            if event["type"] == "final_state":
                final_state = event["data"]

        # Extract answer and citations
        answer = final_state.get("synthesis_result", {}).get("answer", "")
        citations = final_state.get("synthesis_result", {}).get("citations", [])

        # Save query log with traces
        latency_ms = int((time.time() - start_time) * 1000)

        # Serialize traces to JSON
        traces = final_state.get("traces", [])
        trace_json = json.dumps([
            {
                "agent": t.agent if hasattr(t, 'agent') else str(t),
                "action": t.action if hasattr(t, 'action') else "",
                "result": t.result if hasattr(t, 'result') else ""
            }
            for t in traces
        ]) if traces else None

        query_log = QueryLog(
            user_id=current_user.user_id,
            conversation_id=request.conversation_id,
            query=request.message,
            rewritten_query=final_state.get("rewritten_query"),
            answer=answer,
            latency_ms=latency_ms,
            trace_json=trace_json
        )
        db.add(query_log)
        db.flush()  # Get query_log.id without committing

        # Persist agent traces
        for trace in traces:
            agent_trace = AgentTrace(
                query_log_id=query_log.id,
                agent_name=trace.agent if hasattr(trace, 'agent') else "unknown",
                action=trace.action if hasattr(trace, 'action') else "",
                result_summary=trace.result if hasattr(trace, 'result') else ""
            )
            db.add(agent_trace)

        db.commit()

        return {
            "conversation_id": request.conversation_id or "new",
            "message": request.message,
            "response": answer,
            "citations": citations if isinstance(citations, list) else [],
            "latency_ms": latency_ms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/query/stream")
async def chat_query_stream(
    request: ChatRequest,
    current_user: TokenData = Depends(require_role(["viewer", "curator", "admin"])),
    db: Session = Depends(get_db)
):
    """Stream orchestrator output as Server-Sent Events (SSE)."""

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            start_time = time.time()
            final_state = {}

            async for event in orchestrator_module.orchestrator.run(
                query=request.query,
                top_k=request.top_k,
                session_id=request.conversation_id or "default",
                db=db,
                filters=request.filters.model_dump(exclude_none=True) if request.filters else None
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

            # Persist QueryLog with traces
            latency_ms = int((time.time() - start_time) * 1000)
            answer = final_state.get("synthesis_result", {}).get("answer", "")

            # Serialize traces to JSON
            traces = final_state.get("traces", [])
            trace_json = json.dumps([
                {
                    "agent": t.agent if hasattr(t, 'agent') else str(t),
                    "action": t.action if hasattr(t, 'action') else "",
                    "result": t.result if hasattr(t, 'result') else ""
                }
                for t in traces
            ]) if traces else None

            query_log = QueryLog(
                user_id=current_user.user_id,
                conversation_id=request.conversation_id,
                query=request.query,
                rewritten_query=final_state.get("rewritten_query"),
                answer=answer,
                latency_ms=latency_ms,
                trace_json=trace_json
            )
            db.add(query_log)
            db.flush()  # Get query_log.id without committing

            # Persist agent traces
            for trace in traces:
                agent_trace = AgentTrace(
                    query_log_id=query_log.id,
                    agent_name=trace.agent if hasattr(trace, 'agent') else "unknown",
                    action=trace.action if hasattr(trace, 'action') else "",
                    result_summary=trace.result if hasattr(trace, 'result') else ""
                )
                db.add(agent_trace)

            db.commit()

            logger.info(f"Query completed in {latency_ms}ms")

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Stream error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
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
                    "last_query_at": log.created_at.isoformat()
                }
            conversations[conv_id]["query_count"] += 1
            conversations[conv_id]["last_query_at"] = log.created_at.isoformat()

        return {
            "conversations": list(conversations.values()),
            "total": len(conversations)
        }

    except Exception as e:
        logger.error(f"List conversations error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation messages and details."""
    try:
        logs = db.query(QueryLog).filter(
            QueryLog.conversation_id == conversation_id
        ).order_by(QueryLog.created_at).all()

        if not logs:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = []
        for log in logs:
            messages.append({
                "role": "user",
                "content": log.query,
                "timestamp": log.created_at.isoformat()
            })
            messages.append({
                "role": "assistant",
                "content": log.answer,
                "latency_ms": log.latency_ms,
                "timestamp": log.created_at.isoformat()
            })

        return {
            "id": conversation_id,
            "messages": messages,
            "created_at": logs[0].created_at.isoformat() if logs else None,
            "updated_at": logs[-1].created_at.isoformat() if logs else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get conversation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
