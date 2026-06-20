from __future__ import annotations

import json
import re
from typing import Any

from app.agents.base import BaseAgent
from app.core.logging import logger
from app.schemas.models import TraceEvent
from app.schemas.query_state import QueryState
from app.services.llm_provider import llm

SYSTEM_PROMPT = """\
You are a grounding critic. Verify that each factual claim in the answer is supported by one of the numbered sources.

Respond with valid JSON only — no markdown, no explanation:
{
  "confidence": "high" | "medium" | "low",
  "unsupported_claims": ["claim text", ...],
  "note": "one-sentence summary"
}

Confidence levels:
- high: every claim is clearly traceable to at least one source
- medium: most claims are supported; minor inferences or gaps present
- low: one or more significant claims are absent from all sources, or the answer contradicts a source

Be strict: inferences not present in the source text count as unsupported.\
"""


def _build_critic_prompt(answer: str, chunks: list[dict[str, Any]]) -> str:
    sources = "\n\n".join(f"[{i + 1}]: {c.get('text', '')}" for i, c in enumerate(chunks))
    return f"Sources:\n{sources}\n\nAnswer to verify:\n{answer}"


def _parse_verdict(raw: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    logger.warning("Critic: could not parse LLM response as JSON")
    return {"confidence": "low", "unsupported_claims": [], "note": "Critic response could not be parsed."}


class CriticAgent(BaseAgent):
    name = "critic"

    async def execute(self, state: QueryState) -> tuple[QueryState, TraceEvent]:
        synthesis = state.synthesis_result
        answer = synthesis.get("answer", "")
        citations = synthesis.get("citations", [])
        chunks = state.reranked_chunks

        if not answer:
            state.validation = {
                "confidence": "low",
                "note": "No answer generated.",
                "unsupported_claims": [],
                "citation_count": 0,
                "warning": None,
            }
            return state, TraceEvent(agent=self.name, action="validate", result="No answer to validate.")

        if not chunks:
            state.validation = {
                "confidence": "low",
                "note": "No source chunks available to verify answer against.",
                "unsupported_claims": [],
                "citation_count": 0,
                "warning": "Answer could not be verified — no source evidence available.",
            }
            return state, TraceEvent(agent=self.name, action="validate", result="No chunks to verify against.")

        prompt = _build_critic_prompt(answer, chunks)
        raw = await llm.generate(SYSTEM_PROMPT, prompt, temperature=0.1, max_tokens=500)
        verdict = _parse_verdict(raw)

        confidence = verdict.get("confidence", "low")
        unsupported: list[str] = verdict.get("unsupported_claims", [])
        note = verdict.get("note", "")

        warning: str | None = None
        if confidence == "low" and unsupported:
            warning = f"Unsupported claim: {unsupported[0]}"
        elif confidence == "low":
            warning = "Answer may not be fully grounded in the retrieved sources."

        state.validation = {
            "confidence": confidence,
            "note": note,
            "unsupported_claims": unsupported,
            "citation_count": len(citations),
            "warning": warning,
        }

        logger.info(f"Critic: {confidence} — {note}")
        return state, TraceEvent(agent=self.name, action="validate", result=note)
