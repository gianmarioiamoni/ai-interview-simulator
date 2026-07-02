# services/coaching_engine/coaching_diagnostics.py
# CoachingDiagnostics — audit trail for one CoachingEngine cycle (E04-M1)

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from services.coaching_engine.coaching_metrics import CoachingMetrics


class CoachingStage(str, Enum):
    """Ordered stages of a CoachingEngine cycle."""

    GAP_ANALYSIS = "gap_analysis"
    OBJECTIVE_DERIVATION = "objective_derivation"
    ACTION_DERIVATION = "action_derivation"
    RECOMMENDATION_DERIVATION = "recommendation_derivation"
    PLAN_ASSEMBLY = "plan_assembly"


class CoachingStageRecord(BaseModel):
    """Audit record for a single CoachingEngine stage execution."""

    stage: CoachingStage
    completed: bool = Field(default=False)
    skipped: bool = Field(default=False)
    error_message: str | None = Field(default=None)
    duration_ms: float = Field(default=0.0, ge=0.0)

    model_config = {"frozen": True, "extra": "forbid"}


class CoachingDiagnostics(BaseModel):
    """Audit trail for a single CoachingEngine execution.

    Records the outcome of every stage: completed, skipped, or errored.
    Intended for observability, not for driving business logic.

    Invariants (ADR-025):
    - stage_records is ordered by stage sequence.
    - metrics carries the corresponding execution statistics.
    - is_successful reflects overall engine outcome.
    - failure_stage is non-None only when is_successful is False.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    stage_records: tuple[CoachingStageRecord, ...] = Field(default_factory=tuple)
    metrics: CoachingMetrics
    is_successful: bool = Field(default=True)
    failure_stage: CoachingStage | None = Field(default=None)
    failure_reason: str | None = Field(default=None)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def successful(
        cls,
        session_id: str,
        candidate_identity_id: str,
        question_index: int,
        stage_records: tuple[CoachingStageRecord, ...],
        metrics: CoachingMetrics,
    ) -> "CoachingDiagnostics":
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
        stage_records: tuple[CoachingStageRecord, ...],
        metrics: CoachingMetrics,
        failure_stage: CoachingStage,
        failure_reason: str,
    ) -> "CoachingDiagnostics":
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
