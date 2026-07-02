# services/knowledge_pipeline/knowledge_pipeline_metrics.py
# KnowledgePipelineMetrics — execution statistics for one pipeline cycle (E02-M5)

from pydantic import BaseModel, Field


class KnowledgePipelineMetrics(BaseModel):
    """Execution statistics for a single KnowledgePipeline run.

    All durations are in milliseconds. Counts are non-negative integers.
    Immutable once constructed.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    # Stage-level durations (ms)
    extraction_duration_ms: float = Field(default=0.0, ge=0.0)
    store_append_duration_ms: float = Field(default=0.0, ge=0.0)
    feature_engine_duration_ms: float = Field(default=0.0, ge=0.0)
    profile_build_duration_ms: float = Field(default=0.0, ge=0.0)
    total_duration_ms: float = Field(default=0.0, ge=0.0)

    # Stage-level counts
    signals_received: int = Field(default=0, ge=0)
    observations_produced: int = Field(default=0, ge=0)
    observations_in_store: int = Field(default=0, ge=0)
    features_computed: int = Field(default=0, ge=0)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
