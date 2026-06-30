# domain/contracts/reasoning/session_metrics.py

from pydantic import BaseModel, Field


class SessionMetrics(BaseModel):
    """Aggregate session counters maintained by InterviewReasoner.

    All fields are non-negative integers or None.
    Single-writer: InterviewReasoner (ADR-038).
    """

    questions_answered: int = Field(default=0, ge=0)
    follow_up_count: int = Field(default=0, ge=0)
    total_evidence_signals: int = Field(default=0, ge=0)
    positive_evidence_count: int = Field(default=0, ge=0)
    negative_evidence_count: int = Field(default=0, ge=0)
    last_reasoning_at_question_index: int | None = None

    model_config = {"frozen": True, "extra": "forbid"}
