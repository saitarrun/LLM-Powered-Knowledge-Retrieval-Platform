from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

from app.schemas.models import TraceEvent


@dataclass
class RetrievalConfig:
    top_k: int = 5
    filters: dict[str, Any] = field(default_factory=dict)


@dataclass
class QueryState:
    query: str
    session_id: str = "default"
    config: RetrievalConfig = field(default_factory=RetrievalConfig)
    db: Any = None  # SQLAlchemy Session — Any avoids circular import

    # Populated by QueryUnderstandingAgent
    rewritten_query: str = ""
    query_variations: list[str] = field(default_factory=list)
    intent: str = "qa"
    router_decision: str = "vector"

    # Populated by retrieval agents
    retrieved_candidates: list[dict[str, Any]] = field(default_factory=list)

    # Populated by EvidenceAgent
    reranked_chunks: list[dict[str, Any]] = field(default_factory=list)

    # Populated by SynthesisAgent
    synthesis_result: dict[str, Any] = field(default_factory=dict)

    # Populated by CriticAgent
    validation: dict[str, Any] = field(default_factory=dict)

    # Accumulated by Orchestrator
    traces: list[TraceEvent] = field(default_factory=list)
    latency_ms: int = 0
