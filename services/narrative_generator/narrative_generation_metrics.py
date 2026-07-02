# services/narrative_generator/narrative_generation_metrics.py
# NarrativeGenerationMetrics — execution statistics for one generation run (E03-M1, ADR-023)

from pydantic import BaseModel, Field


class NarrativeGenerationMetrics(BaseModel):
    """Execution statistics for a single NarrativeGenerator invocation.

    All durations are in milliseconds. Counts are non-negative integers.
    Immutable once constructed.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    # Timing
    section_build_duration_ms: float = Field(default=0.0, ge=0.0)
    insight_build_duration_ms: float = Field(default=0.0, ge=0.0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)

    # Counts
    features_received: int = Field(default=0, ge=0)
    sections_built: int = Field(default=0, ge=0)
    insights_built: int = Field(default=0, ge=0)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
