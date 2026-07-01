# services/interview_reasoner/profile/dimension_trace_updater.py
"""DimensionTraceUpdater — incremental update of per-dimension aggregates (M2-6C).

Responsibilities:
- Update average_score using a running mean (no score in EvidenceSignal, so
  strength is used as a normalized proxy in [0, 100]).
- Update last_score.
- Increment evidence_count.
- Update last_updated_question.
- Delegate trend computation to TrendUpdater (called by CandidateProfileEngine).

Only dimensions that have new signals are mutated; all others are carried forward
unchanged — incremental O(k) where k = unique dimensions in new_signals.
"""

from __future__ import annotations

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from services.interview_reasoner.profile.base_updater import ProfileUpdater

# PATTERN_DETECTOR signals that carry no new evaluation content should not
# shift the average score (they are derived from existing evidence).
_SCORE_CONTRIBUTING_SOURCES_EXCLUDE: frozenset[EvidenceType] = frozenset({
    EvidenceType.MISSING_EVIDENCE,
    EvidenceType.REPEATED_WEAKNESS,
    EvidenceType.CONFIDENCE_DROP,
    EvidenceType.CONTRADICTORY_ANSWER,
})

_STRENGTH_TO_SCORE_SCALE = 100.0
_MAX_EVIDENCE_CONFIDENCE = 10  # evidence_count at which confidence saturates at 1.0


class DimensionTraceUpdater(ProfileUpdater):
    """Incrementally updates DimensionTrace aggregates for affected dimensions."""

    def update(
        self,
        profile: CandidateProfile,
        new_signals: list[EvidenceSignal],
        question_index: int,
    ) -> CandidateProfile:
        if not new_signals:
            return profile

        # Group score-contributing signals by dimension.
        deltas: dict[ProfileDimension, list[float]] = {}
        for sig in new_signals:
            if sig.signal_type in _SCORE_CONTRIBUTING_SOURCES_EXCLUDE:
                continue
            score = self._signal_to_score(sig)
            deltas.setdefault(sig.dimension, []).append(score)

        if not deltas:
            return profile

        updated_scores = dict(profile.dimension_scores)
        for dim, scores in deltas.items():
            old = updated_scores.get(dim, DimensionTrace())
            updated_scores[dim] = self._merge(old, scores, question_index)

        return profile.model_copy(update={"dimension_scores": updated_scores,
                                          "last_updated_at_question_index": question_index})

    @staticmethod
    def _signal_to_score(sig: EvidenceSignal) -> float:
        """Map signal strength + polarity to a [0, 100] score proxy."""
        base = sig.strength * _STRENGTH_TO_SCORE_SCALE
        return base if sig.polarity == EvidencePolarity.POSITIVE else _STRENGTH_TO_SCORE_SCALE - base

    @staticmethod
    def _merge(old: DimensionTrace, new_scores: list[float], q_idx: int) -> DimensionTrace:
        n_new = len(new_scores)
        n_old = old.evidence_count
        total = n_old + n_new
        new_sum = sum(new_scores)
        avg = (old.average_score * n_old + new_sum) / total
        last = new_scores[-1]
        confidence = min(total / _MAX_EVIDENCE_CONFIDENCE, 1.0)
        return DimensionTrace(
            average_score=round(avg, 2),
            last_score=round(last, 2),
            trend=old.trend,  # TrendUpdater will overwrite this
            confidence=round(confidence, 4),
            evidence_count=total,
            last_updated_question=q_idx,
        )
