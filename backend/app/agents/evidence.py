from typing import Dict, Any, Tuple
from sentence_transformers import CrossEncoder
from app.agents.base import BaseAgent
from app.schemas.models import TraceEvent
from app.core.config import settings
from app.core.logging import logger
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentChunk

class EvidenceAgent(BaseAgent):
    name = "evidence"
    
    def __init__(self):
        logger.info(f"Loading CrossEncoder: {settings.RERANKING_MODEL}")
        self.reranker = CrossEncoder(settings.RERANKING_MODEL)

    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        query = state.get("rewritten_query", state.get("query", ""))
        candidates = state.get("retrieved_candidates", [])
        config = state.get("config", {})
        top_k = config.get("top_k", 5)
        filters = config.get("filters") or {}
        db = state.get("db")
        
        if not candidates:
            state["reranked_chunks"] = []
            return state, TraceEvent(agent=self.name, action="rerank", result="No candidates.")
            
        chunk_ids = [c["metadata"]["chunk_id"] for c in candidates]
        db_chunks = []
        if db is not None:
            query_builder = db.query(DocumentChunk).join(Document).filter(DocumentChunk.id.in_(chunk_ids))

            document_ids = filters.get("document_ids")
            if document_ids:
                query_builder = query_builder.filter(Document.id.in_(document_ids))

            filename_contains = filters.get("filename_contains")
            if filename_contains:
                query_builder = query_builder.filter(Document.filename.ilike(f"%{filename_contains}%"))

            status = filters.get("status")
            if status:
                query_builder = query_builder.filter(Document.status == status)

            if "approval_required" in filters:
                query_builder = query_builder.filter(Document.approval_required == filters["approval_required"])

            approved_by = filters.get("approved_by")
            if approved_by:
                query_builder = query_builder.filter(Document.approved_by == approved_by)

            created_after = filters.get("created_after")
            if created_after:
                query_builder = query_builder.filter(Document.created_at >= created_after)

            created_before = filters.get("created_before")
            if created_before:
                query_builder = query_builder.filter(Document.created_at <= created_before)

            db_chunks = query_builder.all()
        chunk_map = {c.id: c for c in db_chunks}
        document_filters_present = any(
            key in filters
            for key in [
                "document_ids",
                "filename_contains",
                "status",
                "approval_required",
                "approved_by",
                "created_after",
                "created_before",
            ]
        )
        
        valid_candidates = []
        pairs = []
        for c in candidates:
            chunk_id = c["metadata"]["chunk_id"]
            if document_filters_present and chunk_id not in chunk_map:
                continue
            txt = chunk_map[chunk_id].text if chunk_id in chunk_map else c.get("text")
            if txt:
                pairs.append((query, txt))
                valid_candidates.append({
                    "score": c["score"],
                    "metadata": c["metadata"],
                    "text": txt,
                    "db_chunk": chunk_map.get(chunk_id)
                })

        if not pairs:
            state["reranked_chunks"] = valid_candidates[:top_k]
            return state, TraceEvent(agent=self.name, action="skip_rerank", result="No pairs.")
            
        scores = self.reranker.predict(pairs)
        for i, score in enumerate(scores):
            valid_candidates[i]["rerank_score"] = float(score)
            
        valid_candidates.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)
        has_explicit_rerank_threshold = "min_rerank_score" in filters
        min_rerank_score = float(filters.get("min_rerank_score", -5.0))
        final_chunks = [c for c in valid_candidates[:top_k] if c.get("rerank_score", 0) >= min_rerank_score]
        state["reranked_chunks"] = final_chunks if has_explicit_rerank_threshold else (final_chunks or valid_candidates[:top_k])
        
        return state, TraceEvent(agent=self.name, action="rerank", result=f"Selected {len(state['reranked_chunks'])} chunks.")

evidence_agent = EvidenceAgent()
