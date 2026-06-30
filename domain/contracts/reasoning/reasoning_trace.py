# domain/contracts/reasoning/reasoning_trace.py

from pydantic import BaseModel, Field


class ReasoningTraceStep(BaseModel):
    """Metadata for one step in a ReasoningTrace (ADR-041).

    INTERNAL ONLY — never exposed to candidates, reports, or LLM prompts.
    `summary` is a Reasoner-generated label; NEVER contains candidate text.
    """

    step_id: str = Field(..., min_length=1)
    component: str = Field(..., min_length=1, max_length=100)
    rule_name: str = Field(..., min_length=1, max_length=100)
    confidence_delta: float = Field(default=0.0, ge=-1.0, le=1.0)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    # Reasoner-generated descriptor; NEVER contains candidate-supplied text.
    summary: str = Field(default="", max_length=300)

    model_config = {"frozen": True, "extra": "forbid"}


class ReasoningTrace(BaseModel):
    """Internal audit trail for one ReasonerDecision cycle (ADR-041).

    Purpose: debugging, explainability, architecture audits, future replay.

    INTERNAL ONLY:
    - Never rendered in UI or coaching reports.
    - Never sent to NarrativeGenerator or any LLM prompt.
    - Never persisted outside InterviewMemory.reasoning_history.

    Architecture only in V1.1 M2; implementation attached to ReasonerDecision
    in subsequent iteration.
    """

    steps: list[ReasoningTraceStep] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}
