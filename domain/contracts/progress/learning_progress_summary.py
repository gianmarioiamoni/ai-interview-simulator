# domain/contracts/progress/learning_progress_summary.py
# ADR-016A + ADR-022 — LearningProgressSummary (lightweight read-only view)

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from domain.contracts.progress.learning_progress import LearningProgress


class LearningProgressSummary(BaseModel):
    """Lightweight, immutable summary view of a LearningProgress.

    Provides key aggregate properties without carrying full dimensional trend data.
    Suitable for display, logging, and monitoring.

    Mirrors KnowledgeSnapshotSummary / SessionHistorySummary pattern.
    Constraints:
    - No LLM, no business logic, no mutation.
    - Immutable after construction (frozen=True).
    """

    candidate_identity_id: str = Field(..., min_length=1)
    session_count: int = Field(..., ge=0)
    total_questions_answered: int = Field(..., ge=0)
    knowledge_epoch: str = Field(..., min_length=1)
    computed_at: datetime = Field(...)

    mean_confidence_first_session: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_confidence_last_session: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence_delta: float = Field(default=0.0)

    improving_dimensions: int = Field(default=0, ge=0)
    regressing_dimensions: int = Field(default=0, ge=0)

    earliest_session_id: Optional[str] = Field(default=None)
    latest_session_id: Optional[str] = Field(default=None)

    is_empty: bool = Field(default=False)
    schema_version: str = Field(default="1.0", min_length=1)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_progress(cls, progress: LearningProgress) -> "LearningProgressSummary":
        """Produce a lightweight summary from a LearningProgress. Pure derivation."""
        from domain.contracts.progress.learning_progress_statistics import (
            LearningProgressStatistics,
        )

        stats = LearningProgressStatistics.from_progress(progress)

        return cls(
            candidate_identity_id=progress.candidate_identity_id,
            session_count=progress.session_count,
            total_questions_answered=progress.total_questions_answered,
            knowledge_epoch=progress.knowledge_epoch,
            computed_at=progress.computed_at,
            mean_confidence_first_session=stats.mean_confidence_first_session,
            mean_confidence_last_session=stats.mean_confidence_last_session,
            overall_confidence_delta=stats.overall_confidence_delta,
            improving_dimensions=stats.improving_dimensions,
            regressing_dimensions=stats.regressing_dimensions,
            earliest_session_id=(
                progress.earliest_entry.session_id if progress.earliest_entry else None
            ),
            latest_session_id=(
                progress.latest_entry.session_id if progress.latest_entry else None
            ),
            is_empty=progress.is_empty,
            schema_version=progress.schema_version,
        )
