from __future__ import annotations

from abc import ABC, abstractmethod

from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        pass
