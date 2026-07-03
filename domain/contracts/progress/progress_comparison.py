# domain/contracts/progress/progress_comparison.py
# ADR-016A + ADR-022 — ProgressComparison (cross-session profile snapshot comparison)

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from domain.contracts.progress.learning_progress import LearningProgress, SessionProgressEntry


class DimensionalDelta(BaseModel):
    """Confidence delta for one dimension between two sessions.

    Derived by comparing DimensionalScore entries sharing the same feature_type_id.
    """

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    confidence_before: float = Field(..., ge=0.0, le=1.0)
    confidence_after: float = Field(..., ge=0.0, le=1.0)
    delta: float = Field(..., description="confidence_after - confidence_before")
    direction: str = Field(..., description="'improving' | 'regressing' | 'stable'")

    model_config = {"frozen": True, "extra": "forbid"}


class ProgressComparison(BaseModel):
    """Comparison of knowledge state between two session entries.

    Derived from two SessionProgressEntry objects.
    Never modifies SessionHistory, KnowledgeSnapshot, or CandidateProfile.
    Immutable.

    Factory: ProgressComparison.compare()
    """

    candidate_identity_id: str = Field(..., min_length=1)
    session_before_id: str = Field(..., min_length=1)
    session_after_id: str = Field(..., min_length=1)
    session_before_index: int = Field(..., ge=0)
    session_after_index: int = Field(..., ge=0)

    mean_confidence_before: float = Field(..., ge=0.0, le=1.0)
    mean_confidence_after: float = Field(..., ge=0.0, le=1.0)
    overall_delta: float = Field(...)
    overall_direction: str = Field(...)

    dimensional_deltas: tuple[DimensionalDelta, ...] = Field(default_factory=tuple)
    improving_count: int = Field(default=0, ge=0)
    regressing_count: int = Field(default=0, ge=0)
    stable_count: int = Field(default=0, ge=0)
    new_dimensions: tuple[str, ...] = Field(
        default_factory=tuple,
        description="feature_type_ids present after but not before"
    )
    dropped_dimensions: tuple[str, ...] = Field(
        default_factory=tuple,
        description="feature_type_ids present before but not after"
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def compare(
        cls,
        candidate_identity_id: str,
        before: SessionProgressEntry,
        after: SessionProgressEntry,
    ) -> "ProgressComparison":
        """Derive a ProgressComparison from two SessionProgressEntry objects.

        Pure computation. No side effects.
        """
        before_scores = {s.feature_type_id: s for s in before.dimensional_scores}
        after_scores = {s.feature_type_id: s for s in after.dimensional_scores}

        all_ids = set(before_scores) | set(after_scores)
        new_dims = tuple(sorted(fid for fid in after_scores if fid not in before_scores))
        dropped_dims = tuple(sorted(fid for fid in before_scores if fid not in after_scores))
        shared_ids = set(before_scores) & set(after_scores)

        threshold = 0.05
        deltas: list[DimensionalDelta] = []
        for fid in sorted(shared_ids):
            conf_before = before_scores[fid].confidence
            conf_after = after_scores[fid].confidence
            delta = conf_after - conf_before
            if delta > threshold:
                direction = "improving"
            elif delta < -threshold:
                direction = "regressing"
            else:
                direction = "stable"
            deltas.append(DimensionalDelta(
                feature_type_id=fid,
                semantic_category=after_scores[fid].semantic_category,
                confidence_before=conf_before,
                confidence_after=conf_after,
                delta=delta,
                direction=direction,
            ))

        improving = sum(1 for d in deltas if d.direction == "improving")
        regressing = sum(1 for d in deltas if d.direction == "regressing")
        stable = sum(1 for d in deltas if d.direction == "stable")

        overall_delta = after.mean_confidence - before.mean_confidence
        if overall_delta > threshold:
            overall_direction = "improving"
        elif overall_delta < -threshold:
            overall_direction = "regressing"
        else:
            overall_direction = "stable"

        return cls(
            candidate_identity_id=candidate_identity_id,
            session_before_id=before.session_id,
            session_after_id=after.session_id,
            session_before_index=before.session_index,
            session_after_index=after.session_index,
            mean_confidence_before=before.mean_confidence,
            mean_confidence_after=after.mean_confidence,
            overall_delta=overall_delta,
            overall_direction=overall_direction,
            dimensional_deltas=tuple(deltas),
            improving_count=improving,
            regressing_count=regressing,
            stable_count=stable,
            new_dimensions=new_dims,
            dropped_dimensions=dropped_dims,
        )

    @classmethod
    def between_sessions(
        cls,
        progress: LearningProgress,
        before_index: int,
        after_index: int,
    ) -> Optional["ProgressComparison"]:
        """Compare two sessions within a LearningProgress by session_index.

        Returns None if either session_index is not found.
        """
        entries_by_index = {e.session_index: e for e in progress.session_entries}
        before = entries_by_index.get(before_index)
        after = entries_by_index.get(after_index)
        if before is None or after is None:
            return None
        return cls.compare(progress.candidate_identity_id, before, after)
