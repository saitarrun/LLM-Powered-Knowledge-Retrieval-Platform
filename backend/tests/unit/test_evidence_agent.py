from datetime import datetime
from unittest.mock import MagicMock

import pytest

from app.agents.evidence import EvidenceAgent
from app.db.models import Document, DocumentChunk


def add_document_with_chunk(db_session, doc_id, chunk_id, filename, status="indexed", created_at=None):
    document = Document(
        id=doc_id,
        filename=filename,
        content_type="text/plain",
        file_path=f"/tmp/{filename}",
        status=status,
        approval_required=False,
        created_at=created_at or datetime(2026, 1, 1),
    )
    chunk = DocumentChunk(
        id=chunk_id,
        document_id=doc_id,
        text=f"chunk text for {filename}",
        chunk_index=0,
    )
    db_session.add(document)
    db_session.add(chunk)
    db_session.commit()
    return document, chunk


@pytest.mark.asyncio
async def test_evidence_agent_applies_document_filters(db_session):
    """Test evidence filters candidates by document metadata."""
    add_document_with_chunk(db_session, "doc1", "chunk1", "alpha.txt", status="indexed")
    add_document_with_chunk(db_session, "doc2", "chunk2", "beta.txt", status="pending")

    agent = EvidenceAgent()
    agent.reranker = MagicMock()
    agent.reranker.predict.return_value = [1.0]

    state = {
        "query": "alpha",
        "db": db_session,
        "retrieved_candidates": [
            {"score": 0.9, "metadata": {"chunk_id": "chunk1"}},
            {"score": 0.8, "metadata": {"chunk_id": "chunk2"}},
        ],
        "config": {
            "top_k": 5,
            "filters": {
                "document_ids": ["doc1"],
                "status": "indexed",
                "filename_contains": "alpha",
            },
        },
    }

    result_state, trace = await agent.execute(state)

    assert [c["db_chunk"].id for c in result_state["reranked_chunks"]] == ["chunk1"]


@pytest.mark.asyncio
async def test_evidence_agent_applies_min_rerank_score(db_session):
    """Test evidence removes chunks below the configured rerank score."""
    add_document_with_chunk(db_session, "doc1", "chunk1", "alpha.txt")
    add_document_with_chunk(db_session, "doc2", "chunk2", "beta.txt")

    agent = EvidenceAgent()
    agent.reranker = MagicMock()
    agent.reranker.predict.return_value = [0.5, -0.25]

    state = {
        "query": "alpha",
        "db": db_session,
        "retrieved_candidates": [
            {"score": 0.9, "metadata": {"chunk_id": "chunk1"}},
            {"score": 0.8, "metadata": {"chunk_id": "chunk2"}},
        ],
        "config": {
            "top_k": 5,
            "filters": {
                "min_rerank_score": 0.0,
            },
        },
    }

    result_state, trace = await agent.execute(state)

    assert [c["db_chunk"].id for c in result_state["reranked_chunks"]] == ["chunk1"]
