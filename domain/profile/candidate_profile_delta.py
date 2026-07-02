# domain/profile/candidate_profile_delta.py
"""CandidateProfileDelta — field-level change record between two CandidateProfile states.

Used by CandidateProfileComparison to express what changed, not just whether
two profiles differ. Pure computation; no side effects, no persistence.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend


@dataclass(frozen=True)
class DimensionDelta:
    """Change in one dimension between two profile states."""

    dimension: ProfileDimension
    score_delta: float
    """Positive = improvement, negative = regression (before → after)."""
    evidence_delta: int
    """Additional evidence signals observed."""
    trend_before: Trend
    trend_after: Trend
    trend_changed: bool


@dataclass(frozen=True)
class CandidateProfileDelta:
    """Complete change record between a before and after CandidateProfile.

    - dimension_deltas: per-dimension changes (all five dimensions always present).
    - new_areas_covered: areas present in after but absent in before.
    - removed_areas: areas present in before but absent in after (edge case: area re-classification).
    - questions_delta: difference in questions_answered.
    - has_any_change: convenience flag; True when at least one field changed.
    """

    dimension_deltas: tuple[DimensionDelta, ...]
    new_areas_covered: tuple[str, ...]
    removed_areas: tuple[str, ...]
    questions_delta: int
    has_any_change: bool

    @classmethod
    def compute(
        cls,
        before: CandidateProfile,
        after: CandidateProfile,
    ) -> "CandidateProfileDelta":
        """Compute the delta between two profile states."""
        dim_deltas = cls._compute_dimension_deltas(before, after)

        before_areas = set(before.areas_covered)
        after_areas = set(after.areas_covered)
        new_areas = tuple(sorted(after_areas - before_areas))
        removed_areas = tuple(sorted(before_areas - after_areas))

        questions_delta = after.questions_answered - before.questions_answered

        has_change = (
            any(
                d.score_delta != 0.0 or d.evidence_delta != 0 or d.trend_changed
                for d in dim_deltas
            )
            or bool(new_areas)
            or bool(removed_areas)
            or questions_delta != 0
        )

        return cls(
            dimension_deltas=tuple(dim_deltas),
            new_areas_covered=new_areas,
            removed_areas=removed_areas,
            questions_delta=questions_delta,
            has_any_change=has_change,
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @classmethod
    def _compute_dimension_deltas(
        cls,
        before: CandidateProfile,
        after: CandidateProfile,
    ) -> list[DimensionDelta]:
        deltas: list[DimensionDelta] = []
        for dim in ProfileDimension:
            b_trace = before.dimension_scores.get(dim)
            a_trace = after.dimension_scores.get(dim)

            b_score = b_trace.average_score if b_trace else 0.0
            a_score = a_trace.average_score if a_trace else 0.0
            b_ev = b_trace.evidence_count if b_trace else 0
            a_ev = a_trace.evidence_count if a_trace else 0
            b_trend = b_trace.trend if b_trace else Trend.INSUFFICIENT_DATA
            a_trend = a_trace.trend if a_trace else Trend.INSUFFICIENT_DATA

            deltas.append(
                DimensionDelta(
                    dimension=dim,
                    score_delta=round(a_score - b_score, 4),
                    evidence_delta=a_ev - b_ev,
                    trend_before=b_trend,
                    trend_after=a_trend,
                    trend_changed=b_trend != a_trend,
                )
            )
        return deltas
