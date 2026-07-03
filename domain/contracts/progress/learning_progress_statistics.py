# domain/contracts/progress/learning_progress_statistics.py
# ADR-016A + ADR-022 — LearningProgressStatistics (aggregate metrics over LearningProgress)

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from domain.contracts.progress.learning_progress import LearningProgress


class DimensionalTrend(BaseModel):
    """Trend for one knowledge dimension across all sessions.

    Derived from DimensionalScore entries sharing the same feature_type_id.
    """

    feature_type_id: str = Field(..., min_length=1)
    semantic_category: str = Field(..., min_length=1)
    first_confidence: float = Field(..., ge=0.0, le=1.0)
    last_confidence: float = Field(..., ge=0.0, le=1.0)
    delta: float = Field(..., description="last_confidence - first_confidence")
    mean_confidence: float = Field(..., ge=0.0, le=1.0)
    session_count: int = Field(..., ge=0)
    is_improving: bool = Field(default=False)
    is_regressing: bool = Field(default=False)
    is_stable: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}


class LearningProgressStatistics(BaseModel):
    """Aggregate metrics derived from a LearningProgress.

    Pure computation — no LLM, no business logic, no mutation.
    Mirrors KnowledgeSnapshotStatistics / SessionHistoryStatistics patterns.
    """

    candidate_identity_id: str = Field(..., min_length=1)
    session_count: int = Field(..., ge=0)
    total_questions_answered: int = Field(..., ge=0)

    mean_confidence_first_session: float = Field(default=0.0, ge=0.0, le=1.0)
    mean_confidence_last_session: float = Field(default=0.0, ge=0.0, le=1.0)
    overall_confidence_delta: float = Field(
        default=0.0, description="last - first mean confidence"
    )

    unique_feature_type_ids: frozenset[str] = Field(default_factory=frozenset)
    dimensional_trends: tuple[DimensionalTrend, ...] = Field(default_factory=tuple)

    improving_dimensions: int = Field(default=0, ge=0)
    regressing_dimensions: int = Field(default=0, ge=0)
    stable_dimensions: int = Field(default=0, ge=0)

    knowledge_epoch: str = Field(..., min_length=1)
    is_empty: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_progress(cls, progress: LearningProgress) -> "LearningProgressStatistics":
        """Compute statistics from a LearningProgress. Pure derivation."""
        if progress.is_empty:
            return cls(
                candidate_identity_id=progress.candidate_identity_id,
                session_count=0,
                total_questions_answered=0,
                knowledge_epoch=progress.knowledge_epoch,
                is_empty=True,
            )

        entries = progress.session_entries
        first_entry = progress.earliest_entry
        last_entry = progress.latest_entry

        assert first_entry is not None
        assert last_entry is not None

        unique_feature_ids: frozenset[str] = frozenset(
            score.feature_type_id
            for entry in entries
            for score in entry.dimensional_scores
        )

        dimensional_trends = cls._compute_dimensional_trends(entries, unique_feature_ids)
        improving = sum(1 for t in dimensional_trends if t.is_improving)
        regressing = sum(1 for t in dimensional_trends if t.is_regressing)
        stable = sum(1 for t in dimensional_trends if t.is_stable)

        return cls(
            candidate_identity_id=progress.candidate_identity_id,
            session_count=progress.session_count,
            total_questions_answered=progress.total_questions_answered,
            mean_confidence_first_session=first_entry.mean_confidence,
            mean_confidence_last_session=last_entry.mean_confidence,
            overall_confidence_delta=last_entry.mean_confidence - first_entry.mean_confidence,
            unique_feature_type_ids=unique_feature_ids,
            dimensional_trends=tuple(dimensional_trends),
            improving_dimensions=improving,
            regressing_dimensions=regressing,
            stable_dimensions=stable,
            knowledge_epoch=progress.knowledge_epoch,
            is_empty=False,
        )

    @staticmethod
    def _compute_dimensional_trends(
        entries: tuple,
        feature_type_ids: frozenset[str],
    ) -> list[DimensionalTrend]:
        trends: list[DimensionalTrend] = []
        for fid in sorted(feature_type_ids):
            scores = [
                score
                for entry in entries
                for score in entry.dimensional_scores
                if score.feature_type_id == fid
            ]
            if not scores:
                continue
            sorted_scores = sorted(scores, key=lambda s: s.session_index)
            first_conf = sorted_scores[0].confidence
            last_conf = sorted_scores[-1].confidence
            delta = last_conf - first_conf
            mean_conf = sum(s.confidence for s in sorted_scores) / len(sorted_scores)
            semantic_cat = sorted_scores[0].semantic_category
            threshold = 0.05
            trends.append(DimensionalTrend(
                feature_type_id=fid,
                semantic_category=semantic_cat,
                first_confidence=first_conf,
                last_confidence=last_conf,
                delta=delta,
                mean_confidence=mean_conf,
                session_count=len(sorted_scores),
                is_improving=delta > threshold,
                is_regressing=delta < -threshold,
                is_stable=abs(delta) <= threshold,
            ))
        return trends
