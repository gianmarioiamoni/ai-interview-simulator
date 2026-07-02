# domain/profile/candidate_profile_statistics.py
"""CandidateProfileStatistics — computed statistics derived from a CandidateProfile.

Pure computation; no side effects, no persistence.
All methods are stateless class methods operating on immutable inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend


@dataclass(frozen=True)
class DimensionStat:
    """Statistics for a single assessed dimension."""

    dimension: ProfileDimension
    average_score: float
    last_score: float | None
    evidence_count: int
    confidence: float
    trend: Trend


@dataclass(frozen=True)
class ProfileStatisticsResult:
    """Full statistics computed from one CandidateProfile snapshot."""

    dimension_stats: tuple[DimensionStat, ...]
    overall_average_score: float
    assessed_dimension_count: int
    total_evidence_count: int
    dominant_dimension: ProfileDimension | None
    weakest_dimension: ProfileDimension | None
    improving_dimensions: tuple[ProfileDimension, ...]
    declining_dimensions: tuple[ProfileDimension, ...]
    coverage_ratio: float


class CandidateProfileStatistics:
    """Computes statistics from a CandidateProfile.

    Stateless: all logic lives in class methods.
    """

    # All five dimensions are assessable
    _ALL_DIMENSIONS: frozenset[ProfileDimension] = frozenset(ProfileDimension)

    @classmethod
    def compute(cls, profile: CandidateProfile) -> ProfileStatisticsResult:
        """Compute full statistics for a given profile."""
        dimension_stats = cls._compute_dimension_stats(profile)
        scored = [s for s in dimension_stats if s.evidence_count > 0]

        overall_avg = (
            sum(s.average_score for s in scored) / len(scored) if scored else 0.0
        )
        dominant = cls._dominant(scored)
        weakest = cls._weakest(scored)
        improving = tuple(
            s.dimension for s in scored if s.trend == Trend.IMPROVING
        )
        declining = tuple(
            s.dimension for s in scored if s.trend == Trend.DECLINING
        )
        coverage_ratio = len(scored) / len(cls._ALL_DIMENSIONS) if cls._ALL_DIMENSIONS else 0.0

        return ProfileStatisticsResult(
            dimension_stats=tuple(dimension_stats),
            overall_average_score=round(overall_avg, 2),
            assessed_dimension_count=len(scored),
            total_evidence_count=sum(s.evidence_count for s in dimension_stats),
            dominant_dimension=dominant,
            weakest_dimension=weakest,
            improving_dimensions=improving,
            declining_dimensions=declining,
            coverage_ratio=round(coverage_ratio, 4),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @classmethod
    def _compute_dimension_stats(
        cls, profile: CandidateProfile
    ) -> list[DimensionStat]:
        stats: list[DimensionStat] = []
        for dim in ProfileDimension:
            trace: DimensionTrace | None = profile.dimension_scores.get(dim)
            if trace is None:
                stats.append(
                    DimensionStat(
                        dimension=dim,
                        average_score=0.0,
                        last_score=None,
                        evidence_count=0,
                        confidence=0.0,
                        trend=Trend.INSUFFICIENT_DATA,
                    )
                )
            else:
                stats.append(
                    DimensionStat(
                        dimension=dim,
                        average_score=trace.average_score,
                        last_score=trace.last_score,
                        evidence_count=trace.evidence_count,
                        confidence=trace.confidence,
                        trend=trace.trend,
                    )
                )
        return stats

    @classmethod
    def _dominant(cls, scored: list[DimensionStat]) -> ProfileDimension | None:
        if not scored:
            return None
        return max(scored, key=lambda s: s.average_score).dimension

    @classmethod
    def _weakest(cls, scored: list[DimensionStat]) -> ProfileDimension | None:
        if not scored:
            return None
        return min(scored, key=lambda s: s.average_score).dimension
