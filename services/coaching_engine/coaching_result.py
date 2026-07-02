# services/coaching_engine/coaching_result.py
# CoachingResult — immutable output of a CoachingEngine cycle (E04-M1)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from services.coaching_engine.coaching_diagnostics import CoachingDiagnostics


class CoachingResult(BaseModel):
    """Immutable output of a single CoachingEngine run.

    Contains the assembled CoachingSnapshot (CoachingPlan) and full
    diagnostics for this cycle.

    Invariants (ADR-025):
    - snapshot is always present (may be an empty snapshot on failure).
    - diagnostics is always present regardless of success/failure.
    - failure_reason is non-None only when is_successful is False.
    - CandidateProfile is never stored here; it is an input only.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    snapshot: CoachingSnapshot = Field(
        ..., description="Assembled CoachingPlan; may be empty on failure."
    )
    diagnostics: CoachingDiagnostics = Field(
        ..., description="Full audit trail for this engine cycle."
    )
    is_successful: bool = Field(default=True)
    failure_reason: str | None = Field(default=None)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    @property
    def has_objectives(self) -> bool:
        return self.snapshot.statistics.total_objectives > 0

    @property
    def objective_count(self) -> int:
        return self.snapshot.statistics.total_objectives

    @property
    def action_count(self) -> int:
        return self.snapshot.statistics.total_actions

    @property
    def recommendation_count(self) -> int:
        return self.snapshot.statistics.total_recommendations
