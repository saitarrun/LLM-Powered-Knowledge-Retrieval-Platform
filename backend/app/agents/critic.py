from typing import Dict, Any, Tuple
from app.agents.base import BaseAgent
from app.schemas.models import TraceEvent
from app.core.logging import logger


class CriticAgent(BaseAgent):
    name = "critic"

    async def execute(self, state: Dict[str, Any]) -> Tuple[Dict[str, Any], TraceEvent]:
        synthesis = state.get("synthesis_result", {})
        citations = synthesis.get("citations", [])
        answer = synthesis.get("answer", "")

        if not answer:
            confidence = "low"
            note = "No answer generated."
        elif not citations:
            confidence = "low"
            note = "Answer has no citations — may not be grounded in sources."
        else:
            confidence = "high"
            note = f"Answer grounded in {len(citations)} source(s)."

        state["validation"] = {
            "confidence": confidence,
            "note": note,
            "citation_count": len(citations)
        }

        logger.info(f"Critic validation: {confidence} - {note}")

        return state, TraceEvent(
            agent=self.name,
            action="validate",
            result=note
        )
