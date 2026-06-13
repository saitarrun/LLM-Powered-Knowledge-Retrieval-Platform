from abc import ABC, abstractmethod
from typing import Any

from app.schemas.models import TraceEvent


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def execute(self, state: dict[str, Any]) -> tuple[dict[str, Any], TraceEvent]:
        """
        Execute the agent's logic.
        Returns updated state and a trace event.
        """
        pass
