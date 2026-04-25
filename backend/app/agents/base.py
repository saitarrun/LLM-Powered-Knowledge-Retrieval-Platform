from abc import ABC, abstractmethod
from typing import Dict, Any, Tuple
from app.schemas.models import TraceEvent


class BaseAgent(ABC):
    name: str = "base"

    @abstractmethod
    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        """
        Execute the agent's logic.
        Returns updated state and a trace event.
        """
        pass
