# domain/profile/candidate_profile_comparison.py
"""CandidateProfileComparison — structural equality and semantic comparison of two profiles.

Distinct from CandidateProfileDelta:
- Delta: what changed (quantities, directions).
- Comparison: are they equal? what is the similarity?  who is stronger?

Pure computation; no side effects, no persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.profile.candidate_profile_delta import CandidateProfileDelta


class ComparisonVerdict(str, Enum):
    """Overall verdict when comparing two profiles."""

    IDENTICAL = "identical"
    IMPROVED = "improved"
    REGRESSED = "regressed"
    MIXED = "mixed"
    INSUFFICIENT_DATA = "insufficient_data"


@dataclass(frozen=True)
class DimensionComparison:
    """Pairwise comparison result for one dimension."""

    dimension: ProfileDimension
    left_score: float
    right_score: float
    score_diff: float
    """right_score - left_score. Positive = right is stronger."""
    left_is_stronger: bool
    right_is_stronger: bool
    are_equal: bool


@dataclass(frozen=True)
class ProfileComparisonResult:
    """Full comparison result between two CandidateProfile objects."""

    are_identical: bool
    """True if both profiles produce the same observable values."""
    verdict: ComparisonVerdict
    dimension_comparisons: tuple[DimensionComparison, ...]
    improved_dimensions: tuple[ProfileDimension, ...]
    """Dimensions where right > left."""
    regressed_dimensions: tuple[ProfileDimension, ...]
    """Dimensions where right < left."""
    equal_dimensions: tuple[ProfileDimension, ...]
    overall_score_left: float
    overall_score_right: float
    overall_score_diff: float
    delta: CandidateProfileDelta


class CandidateProfileComparison:
    """Compares two CandidateProfile instances.

    left  = baseline (earlier / reference)
    right = candidate (later / updated)

    Stateless: all logic in class methods.
    """

    _EQUALITY_TOLERANCE: float = 0.01

    @classmethod
    def compare(
        cls,
        left: CandidateProfile,
        right: CandidateProfile,
    ) -> ProfileComparisonResult:
        """Compare two profiles and return a full comparison report."""
        delta = CandidateProfileDelta.compute(left, right)
        dim_comparisons = cls._compare_dimensions(left, right)

        improved = tuple(d.dimension for d in dim_comparisons if d.right_is_stronger)
        regressed = tuple(d.dimension for d in dim_comparisons if d.left_is_stronger)
        equal_dims = tuple(d.dimension for d in dim_comparisons if d.are_equal)

        scored_left = [d.left_score for d in dim_comparisons if d.left_score > 0.0]
        scored_right = [d.right_score for d in dim_comparisons if d.right_score > 0.0]
        avg_left = sum(scored_left) / len(scored_left) if scored_left else 0.0
        avg_right = sum(scored_right) / len(scored_right) if scored_right else 0.0

        are_identical = not delta.has_any_change
        verdict = cls._verdict(improved, regressed, avg_left, avg_right)

        return ProfileComparisonResult(
            are_identical=are_identical,
            verdict=verdict,
            dimension_comparisons=tuple(dim_comparisons),
            improved_dimensions=improved,
            regressed_dimensions=regressed,
            equal_dimensions=equal_dims,
            overall_score_left=round(avg_left, 2),
            overall_score_right=round(avg_right, 2),
            overall_score_diff=round(avg_right - avg_left, 2),
            delta=delta,
        )

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    @classmethod
    def _compare_dimensions(
        cls,
        left: CandidateProfile,
        right: CandidateProfile,
    ) -> list[DimensionComparison]:
        comparisons: list[DimensionComparison] = []
        for dim in ProfileDimension:
            l_trace = left.dimension_scores.get(dim)
            r_trace = right.dimension_scores.get(dim)
            l_score = l_trace.average_score if l_trace else 0.0
            r_score = r_trace.average_score if r_trace else 0.0
            diff = round(r_score - l_score, 4)
            are_equal = abs(diff) < cls._EQUALITY_TOLERANCE
            comparisons.append(
                DimensionComparison(
                    dimension=dim,
                    left_score=l_score,
                    right_score=r_score,
                    score_diff=diff,
                    left_is_stronger=diff < -cls._EQUALITY_TOLERANCE,
                    right_is_stronger=diff > cls._EQUALITY_TOLERANCE,
                    are_equal=are_equal,
                )
            )
        return comparisons

    @classmethod
    def _verdict(
        cls,
        improved: tuple[ProfileDimension, ...],
        regressed: tuple[ProfileDimension, ...],
        avg_left: float,
        avg_right: float,
    ) -> ComparisonVerdict:
        if avg_left == 0.0 and avg_right == 0.0:
            return ComparisonVerdict.INSUFFICIENT_DATA
        if not improved and not regressed:
            return ComparisonVerdict.IDENTICAL
        if improved and not regressed:
            return ComparisonVerdict.IMPROVED
        if regressed and not improved:
            return ComparisonVerdict.REGRESSED
        return ComparisonVerdict.MIXED
