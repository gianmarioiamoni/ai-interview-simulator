# tests/performance/stub_llm.py
# EPIC-V13-09 C1 — deterministic stub LLM for written-cycle SLO-Q harness (AR-16).

from __future__ import annotations

import json
from typing import Type, TypeVar

from pydantic import BaseModel

from app.ports.llm_port import LLMPort, LLMResponse

T = TypeVar("T", bound=BaseModel)

# Score ≥ CODING_QUALITY_IMPROVEMENT_THRESHOLD skips AnswerImprover second call.
DEFAULT_WRITTEN_EVALUATION_JSON = json.dumps(
    {
        "score": 95.0,
        "feedback": "Solid written answer covering the core concepts.",
        "strengths": ["Clear structure"],
        "weaknesses": [],
        "clarification_needed": False,
        "follow_up_question": None,
    }
)


class _StubLLMResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class DeterministicStubLLM(LLMPort):
    """Scripted LLMPort for harnesses; no network I/O."""

    def __init__(
        self,
        scripted_responses: list[str] | None = None,
    ) -> None:
        self._responses = list(
            scripted_responses
            if scripted_responses is not None
            else [DEFAULT_WRITTEN_EVALUATION_JSON]
        )
        self._index = 0
        self.invoke_call_count = 0

    def invoke(
        self,
        prompt: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        del prompt, system_prompt
        if self._index >= len(self._responses):
            raise RuntimeError("No more scripted LLM responses.")
        content = self._responses[self._index]
        self._index += 1
        self.invoke_call_count += 1
        return _StubLLMResponse(content)

    def invoke_json(
        self,
        prompt: str,
        schema: Type[T],
    ) -> T:
        del prompt, schema
        raise ValueError("structured output unused in SLO-Q stub path")

    def reset(self) -> None:
        self._index = 0
        self.invoke_call_count = 0
