# services/knowledge_pipeline/knowledge_pipeline_diagnostics.py
# KnowledgePipelineDiagnostics — audit trail for one pipeline cycle (E02-M5)

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from services.knowledge_pipeline.knowledge_pipeline_metrics import KnowledgePipelineMetrics


class PipelineStage(str, Enum):
    """Ordered pipeline stages for audit trail entries."""

    EXTRACTION = "extraction"
    STORE_APPEND = "store_append"
    QUERY_ENGINE = "query_engine"
    FEATURE_ENGINE = "feature_engine"
    PROFILE_BUILD = "profile_build"


class StageAuditRecord(BaseModel):
    """Audit record for a single pipeline stage execution."""

    stage: PipelineStage
    completed: bool = Field(default=False)
    skipped: bool = Field(default=False)
    error_message: str | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)

    model_config = {"frozen": True, "extra": "forbid"}


class KnowledgePipelineDiagnostics(BaseModel):
    """Audit trail for a single KnowledgePipeline execution.

    Records the outcome of every stage: completed, skipped, or errored.
    Intended for observability, not for driving business logic.

    Invariants:
    - stage_records is ordered by pipeline stage sequence.
    - metrics carries the corresponding execution statistics.
    - is_successful reflects overall pipeline outcome.
    - failure_stage is non-None only when is_successful is False.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    stage_records: tuple[StageAuditRecord, ...] = Field(default_factory=tuple)
    metrics: KnowledgePipelineMetrics
    is_successful: bool = Field(default=True)
    failure_stage: PipelineStage | None = Field(
        default=None,
        description="Stage at which the pipeline failed, if any.",
    )
    failure_reason: str | None = Field(default=None)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def successful(
        cls,
        session_id: str,
        candidate_identity_id: str,
        question_index: int,
        stage_records: tuple[StageAuditRecord, ...],
        metrics: KnowledgePipelineMetrics,
    ) -> "KnowledgePipelineDiagnostics":
        return cls(
            session_id=session_id,
            candidate_identity_id=candidate_identity_id,
            question_index=question_index,
            stage_records=stage_records,
            metrics=metrics,
            is_successful=True,
        )

    @classmethod
    def failed(
        cls,
        session_id: str,
        candidate_identity_id: str,
        question_index: int,
        stage_records: tuple[StageAuditRecord, ...],
        metrics: KnowledgePipelineMetrics,
        failure_stage: PipelineStage,
        failure_reason: str,
    ) -> "KnowledgePipelineDiagnostics":
        return cls(
            session_id=session_id,
            candidate_identity_id=candidate_identity_id,
            question_index=question_index,
            stage_records=stage_records,
            metrics=metrics,
            is_successful=False,
            failure_stage=failure_stage,
            failure_reason=failure_reason,
        )
