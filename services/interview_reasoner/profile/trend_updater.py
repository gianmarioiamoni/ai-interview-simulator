# services/interview_reasoner/profile/trend_updater.py
"""TrendUpdater — per-dimension trend computation (M2-6C).

Algorithm:
  - Requires at least 3 evidence points to assign IMPROVING / DECLINING.
  - Compares the last score against the running average:
      last > avg + THRESHOLD → IMPROVING
      last < avg - THRESHOLD → DECLINING
      otherwise              → STABLE
  - Fewer than 3 observations → INSUFFICIENT_DATA.

Fully deterministic. O(k) in updated dimensions.
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.profile.base_updater import ProfileUpdater
from domain.contracts.reasoning.evidence_signal import EvidenceSignal

_MIN_EVIDENCE_FOR_TREND = 3
_TREND_THRESHOLD = 8.0  # score-point delta to qualify as IMPROVING / DECLINING


class TrendUpdater(ProfileUpdater):
    """Computes per-dimension trend from current DimensionTrace aggregates."""

    def update(
        self,
        profile: CandidateProfile,
        new_signals: list[EvidenceSignal],
        question_index: int,
    ) -> CandidateProfile:
        if not profile.dimension_scores:
            return profile

        updated: dict[ProfileDimension, DimensionTrace] = {}
        changed = False
        for dim, trace in profile.dimension_scores.items():
            new_trend = self._compute_trend(trace)
            if new_trend != trace.trend:
                updated[dim] = trace.model_copy(update={"trend": new_trend})
                changed = True
            else:
                updated[dim] = trace

        if not changed:
            return profile

        return profile.model_copy(update={"dimension_scores": updated})

    @staticmethod
    def _compute_trend(trace: DimensionTrace) -> Trend:
        if trace.evidence_count < _MIN_EVIDENCE_FOR_TREND or trace.last_score is None:
            return Trend.INSUFFICIENT_DATA
        delta = trace.last_score - trace.average_score
        if delta > _TREND_THRESHOLD:
            return Trend.IMPROVING
        if delta < -_TREND_THRESHOLD:
            return Trend.DECLINING
        return Trend.STABLE
