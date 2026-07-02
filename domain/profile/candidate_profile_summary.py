# domain/profile/candidate_profile_summary.py
"""CandidateProfileSummary — structured human-readable summary of a CandidateProfile.

Derives a machine-structured summary (no free text, no AI generation).
All labels are deterministic from profile values.
No Narrative. No Coaching. No persistence.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from domain.profile.candidate_profile_statistics import (
    CandidateProfileStatistics,
    ProfileStatisticsResult,
)


class ProfileMaturityLevel(str, Enum):
    """Overall maturity of a profile based on evidence coverage."""

    EMPTY = "empty"
    EARLY = "early"
    DEVELOPING = "developing"
    MATURE = "mature"
    COMPLETE = "complete"


class Scoreband(str, Enum):
    """Discrete score band for a dimension or overall score."""

    VERY_LOW = "very_low"
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


@dataclass(frozen=True)
class DimensionSummaryEntry:
    """Summarized state of one dimension."""

    dimension: ProfileDimension
    scoreband: Scoreband
    trend: Trend
    is_assessed: bool
    confidence: float


@dataclass(frozen=True)
class ProfileSummaryResult:
    """Structured summary of a CandidateProfile.

    Fully derived from profile values — no free text, no AI, no persistence.
    """

    maturity: ProfileMaturityLevel
    overall_scoreband: Scoreband
    dimension_entries: tuple[DimensionSummaryEntry, ...]
    assessed_count: int
    questions_answered: int
    areas_covered: tuple[str, ...]
    dominant_dimension: ProfileDimension | None
    weakest_dimension: ProfileDimension | None
    has_improving_trend: bool
    has_declining_trend: bool
    is_data_sufficient: bool
    """True when at least 3 dimensions are assessed with evidence."""


class CandidateProfileSummary:
    """Produces a structured summary from a CandidateProfile.

    Stateless: all logic in class methods.
    """

    _MIN_DIMENSIONS_FOR_SUFFICIENCY: int = 3
    _MATURITY_THRESHOLDS: tuple[tuple[int, ProfileMaturityLevel], ...] = (
        (0, ProfileMaturityLevel.EMPTY),
        (1, ProfileMaturityLevel.EARLY),
        (2, ProfileMaturityLevel.DEVELOPING),
        (4, ProfileMaturityLevel.MATURE),
        (5, ProfileMaturityLevel.COMPLETE),
    )

    @classmethod
    def summarize(cls, profile: CandidateProfile) -> ProfileSummaryResult:
        """Produce a structured summary of the given profile."""
        stats: ProfileStatisticsResult = CandidateProfileStatistics.compute(profile)

        maturity = cls._maturity(stats.assessed_dimension_count)
        overall_scoreband = cls._scoreband(stats.overall_average_score)
        dimension_entries = cls._dimension_entries(stats)

        return ProfileSummaryResult(
            maturity=maturity,
            overall_scoreband=overall_scoreband,
            dimension_entries=dimension_entries,
            assessed_count=stats.assessed_dimension_count,
            questions_answered=profile.questions_answered,
            areas_covered=tuple(profile.areas_covered),
            dominant_dimension=stats.dominant_dimension,
            weakest_dimension=stats.weakest_dimension,
            has_improving_trend=bool(stats.improving_dimensions),
            has_declining_trend=bool(stats.declining_dimensions),
            is_data_sufficient=(
                stats.assessed_dimension_count >= cls._MIN_DIMENSIONS_FOR_SUFFICIENCY
            ),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @classmethod
    def _maturity(cls, assessed_count: int) -> ProfileMaturityLevel:
        result = ProfileMaturityLevel.EMPTY
        for threshold, level in cls._MATURITY_THRESHOLDS:
            if assessed_count >= threshold:
                result = level
        return result

    @classmethod
    def _scoreband(cls, score: float) -> Scoreband:
        if score >= 80.0:
            return Scoreband.VERY_HIGH
        if score >= 65.0:
            return Scoreband.HIGH
        if score >= 45.0:
            return Scoreband.MODERATE
        if score >= 25.0:
            return Scoreband.LOW
        return Scoreband.VERY_LOW

    @classmethod
    def _dimension_entries(
        cls, stats: ProfileStatisticsResult
    ) -> tuple[DimensionSummaryEntry, ...]:
        entries: list[DimensionSummaryEntry] = []
        for dim_stat in stats.dimension_stats:
            entries.append(
                DimensionSummaryEntry(
                    dimension=dim_stat.dimension,
                    scoreband=cls._scoreband(dim_stat.average_score),
                    trend=dim_stat.trend,
                    is_assessed=dim_stat.evidence_count > 0,
                    confidence=dim_stat.confidence,
                )
            )
        return tuple(entries)
