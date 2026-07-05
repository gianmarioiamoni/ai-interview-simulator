# domain/contracts/interview/generation_metadata.py

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerationMetadata(BaseModel):
    """Immutable summary of LLM generation metrics for a session.

    Snapshot of observable execution metrics captured at session close.
    Used for report display and audit only; not used for scoring or routing.
    All cost fields are Optional because sessions where EvaluationAggregateNode
    was bypassed or cost tracking was disabled produce no cost data.
    """

    model_config = {"frozen": True, "extra": "forbid"}

    total_tokens_used: int = Field(ge=0)
    total_cost_usd: float | None = Field(default=None, ge=0.0)
    cost_per_question_usd: float | None = Field(default=None, ge=0.0)
    schema_version: str = Field(default="1.0", min_length=1)
