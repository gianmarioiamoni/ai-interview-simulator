# services/interview_pipeline/interview_pipeline_metrics.py
# InterviewPipelineMetrics — execution statistics for one pipeline invocation

from __future__ import annotations

from pydantic import BaseModel, Field


class InterviewPipelineMetrics(BaseModel):
    """Execution statistics for a single InterviewPipeline run.

    All durations are in milliseconds. Counts are non-negative integers.
    Immutable once constructed.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    # Stage-level durations (ms)
    knowledge_pipeline_duration_ms: float = Field(default=0.0, ge=0.0)
    narrative_generator_duration_ms: float = Field(default=0.0, ge=0.0)
    coaching_engine_duration_ms: float = Field(default=0.0, ge=0.0)
    session_close_duration_ms: float = Field(default=0.0, ge=0.0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)

    # Stage-level counts
    signals_received: int = Field(default=0, ge=0)
    features_produced: int = Field(default=0, ge=0)
    sections_built: int = Field(default=0, ge=0)
    insights_built: int = Field(default=0, ge=0)
    coaching_objectives_produced: int = Field(default=0, ge=0)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
