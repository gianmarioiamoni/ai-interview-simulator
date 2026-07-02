# services/narrative_generator/narrative_generation_diagnostics.py
# NarrativeGenerationDiagnostics — audit trail for one generation run (E03-M1, ADR-023)

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from services.narrative_generator.narrative_generation_metrics import NarrativeGenerationMetrics


class NarrativeStage(str, Enum):
    """Ordered generation stages for audit trail entries."""

    CONTEXT_VALIDATION = "context_validation"
    SECTION_BUILD = "section_build"
    INSIGHT_BUILD = "insight_build"
    NARRATIVE_ASSEMBLY = "narrative_assembly"


class StageAuditRecord(BaseModel):
    """Audit record for a single generation stage execution."""

    stage: NarrativeStage
    completed: bool = Field(default=False)
    skipped: bool = Field(default=False)
    error_message: str | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)

    model_config = {"frozen": True, "extra": "forbid"}


class NarrativeGenerationDiagnostics(BaseModel):
    """Audit trail for a single NarrativeGenerator invocation.

    Records the outcome of every stage: completed, skipped, or errored.
    Intended for observability, not for driving business logic.

    Invariants:
    - stage_records is ordered by generation stage sequence.
    - metrics carries the corresponding execution statistics.
    - is_successful reflects overall generation outcome.
    - failure_stage is non-None only when is_successful is False.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    stage_records: tuple[StageAuditRecord, ...] = Field(default_factory=tuple)
    metrics: NarrativeGenerationMetrics
    is_successful: bool = Field(default=True)
    failure_stage: NarrativeStage | None = Field(default=None)
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
        metrics: NarrativeGenerationMetrics,
    ) -> "NarrativeGenerationDiagnostics":
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
        metrics: NarrativeGenerationMetrics,
        failure_stage: NarrativeStage,
        failure_reason: str,
    ) -> "NarrativeGenerationDiagnostics":
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
