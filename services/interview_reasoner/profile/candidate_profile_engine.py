# services/interview_reasoner/profile/candidate_profile_engine.py
"""CandidateProfileEngine — single entry-point for CandidateProfile evolution (M2-6C).

Exposes ONE public method: update().

Internally orchestrates a fixed pipeline of focused updaters:

  1. DimensionTraceUpdater  — running score aggregates per dimension
  2. TrendUpdater           — per-dimension trend classification
  3. CoverageUpdater        — questions_answered + areas_covered
  4. DominantDimensionCalculator — session-scoped dominant dimension (read-only)

The engine is stateless.  All state flows through CandidateProfile (immutable).

Design constraints (ADR-037):
- Only CandidateProfileEngine writes CandidateProfile.
- ReasonerService calls this engine; the graph is unaware of profile update details.
- Never O(|EvidenceStore|). Always O(|new_signals|).
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.profile.coverage_updater import CoverageUpdater
from services.interview_reasoner.profile.dimension_trace_updater import DimensionTraceUpdater
from services.interview_reasoner.profile.dominant_dimension_calculator import (
    DominantDimensionCalculator,
)
from services.interview_reasoner.profile.trend_updater import TrendUpdater


class CandidateProfileEngine:
    """Orchestrates incremental CandidateProfile updates.

    Usage::

        engine = CandidateProfileEngine()
        new_profile = engine.update(old_profile, new_signals, question_index)
    """

    def __init__(self) -> None:
        self._dim_updater = DimensionTraceUpdater()
        self._trend_updater = TrendUpdater()
        self._coverage_updater = CoverageUpdater()
        self._dominant_calc = DominantDimensionCalculator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(
        self,
        profile: CandidateProfile,
        new_signals: list[EvidenceSignal],
        question_index: int,
    ) -> CandidateProfile:
        """Return an updated CandidateProfile.

        Applies updaters in fixed order:
          DimensionTrace → Trend → Coverage

        The profile returned is always a distinct immutable object when any
        change occurred; the original is never mutated.
        """
        if not new_signals:
            return profile

        # Capture before DimensionTraceUpdater stamps last_updated_at_question_index.
        prev_last_updated = profile.last_updated_at_question_index

        profile = self._dim_updater.update(profile, new_signals, question_index)
        profile = self._trend_updater.update(profile, new_signals, question_index)
        profile = self._coverage_updater.update(
            profile, new_signals, question_index, prev_last_updated
        )

        return profile

    def dominant_dimension(
        self,
        profile: CandidateProfile,
    ) -> ProfileDimension | None:
        """Return the session-scoped dominant dimension from accumulated profile.

        Delegates to DominantDimensionCalculator for full-session coverage
        (not just current-cycle signals).
        """
        return self._dominant_calc.calculate(profile)
