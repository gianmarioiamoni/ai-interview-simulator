# services/coaching_engine/coaching_metrics.py
# CoachingMetrics — execution statistics for one CoachingEngine cycle (E04-M1)

from pydantic import BaseModel, Field


class CoachingMetrics(BaseModel):
    """Execution statistics for a single CoachingEngine run.

    All durations are in milliseconds. Counts are non-negative integers.
    Immutable once constructed.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    # Stage-level durations (ms)
    gap_analysis_duration_ms: float = Field(default=0.0, ge=0.0)
    objective_derivation_duration_ms: float = Field(default=0.0, ge=0.0)
    action_derivation_duration_ms: float = Field(default=0.0, ge=0.0)
    recommendation_derivation_duration_ms: float = Field(default=0.0, ge=0.0)
    plan_assembly_duration_ms: float = Field(default=0.0, ge=0.0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)

    # Output counts
    features_consumed: int = Field(default=0, ge=0)
    knowledge_gaps_referenced: int = Field(default=0, ge=0)
    objectives_produced: int = Field(default=0, ge=0)
    actions_produced: int = Field(default=0, ge=0)
    recommendations_produced: int = Field(default=0, ge=0)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
