from __future__ import annotations

import json

from sqlalchemy.orm import Session

from app.db.models import AgentTrace, Document, DocumentChunk, QueryLog
from app.schemas.query_state import QueryState


class ChunkRepository:
    """Data-access object for DocumentChunk queries.

    Keeps SQL logic out of agents. Stateless — each method receives the
    per-request session so the repository itself is a safe singleton.
    """

    def fetch_chunks(
        self,
        db: Session,
        ids: list[str],
        filters: dict,
    ) -> list[DocumentChunk]:
        """Return chunks matching ids, optionally filtered by document metadata."""
        query_builder = (
            db.query(DocumentChunk)
            .join(Document)
            .filter(DocumentChunk.id.in_(ids))
        )

        if document_ids := filters.get("document_ids"):
            query_builder = query_builder.filter(Document.id.in_(document_ids))

        if filename_contains := filters.get("filename_contains"):
            query_builder = query_builder.filter(
                Document.filename.ilike(f"%{filename_contains}%")
            )

        if status := filters.get("status"):
            query_builder = query_builder.filter(Document.status == status)

        if "approval_required" in filters:
            query_builder = query_builder.filter(
                Document.approval_required == filters["approval_required"]
            )

        if approved_by := filters.get("approved_by"):
            query_builder = query_builder.filter(Document.approved_by == approved_by)

        if created_after := filters.get("created_after"):
            query_builder = query_builder.filter(Document.created_at >= created_after)

        if created_before := filters.get("created_before"):
            query_builder = query_builder.filter(Document.created_at <= created_before)

        return query_builder.all()


chunk_repository = ChunkRepository()


class QueryLogRepository:
    """Persists a completed query and its agent traces.

    Centralises the serialization + DB write that was previously duplicated
    in both the /chat and /chat/query/stream route handlers.
    """

    def persist(
        self,
        db: Session,
        state: QueryState,
        user_id: str | None,
        conversation_id: str | None,
        latency_ms: int,
    ) -> QueryLog:
        traces = state.traces
        trace_json = (
            json.dumps(
                [
                    {
                        "agent": t.agent,
                        "action": t.action,
                        "result": t.result,
                    }
                    for t in traces
                ]
            )
            if traces
            else None
        )

        answer = state.synthesis_result.get("answer", "")

        query_log = QueryLog(
            user_id=user_id,
            conversation_id=conversation_id,
            query=state.query,
            rewritten_query=state.rewritten_query or None,
            answer=answer,
            latency_ms=latency_ms,
            trace_json=trace_json,
        )
        db.add(query_log)
        db.flush()

        for trace in traces:
            db.add(
                AgentTrace(
                    query_log_id=query_log.id,
                    agent_name=trace.agent,
                    action=trace.action,
                    result_summary=trace.result,
                )
            )

        db.commit()
        return query_log


query_log_repository = QueryLogRepository()
