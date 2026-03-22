from typing import Dict, Any, Tuple
from sentence_transformers import CrossEncoder
from app.agents.base import BaseAgent
from app.schemas.models import TraceEvent
from app.core.config import settings
from app.core.logging import logger
from sqlalchemy.orm import Session
from app.db.models import DocumentChunk

class EvidenceAgent(BaseAgent):
    name = "evidence"
    
    def __init__(self):
        logger.info(f"Loading CrossEncoder: {settings.RERANKING_MODEL}")
        self.reranker = CrossEncoder(settings.RERANKING_MODEL)

    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        query = state.get("rewritten_query", state.get("query", ""))
        candidates = state.get("retrieved_candidates", [])
        top_k = state.get("config", {}).get("top_k", 5)
        db = state.get("db")
        
        if not candidates:
            state["reranked_chunks"] = []
            return state, TraceEvent(agent=self.name, action="rerank", result="No candidates.")
            
        chunk_ids = [c["metadata"]["chunk_id"] for c in candidates]
        db_chunks = db.query(DocumentChunk).filter(DocumentChunk.id.in_(chunk_ids)).all()
        chunk_map = {c.id: c for c in db_chunks}
        
        valid_candidates = []
        pairs = []
        for c in candidates:
            chunk_id = c["metadata"]["chunk_id"]
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
        final_chunks = [c for c in valid_candidates[:top_k] if c.get("rerank_score", 0) > -5.0]
        state["reranked_chunks"] = final_chunks or valid_candidates[:top_k]
        
        return state, TraceEvent(agent=self.name, action="rerank", result=f"Selected {len(state['reranked_chunks'])} chunks.")

evidence_agent = EvidenceAgent()
