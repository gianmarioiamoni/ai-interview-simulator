# services/interview_reasoner/pattern_detection/detectors/trend_detector.py
"""TrendDetector — analyses score and confidence trends across the session (ADR-034).

Algorithm (fully deterministic, O(n)):
Sources: DimensionTrace (CandidateProfile), ReasoningHistory, EvidenceStore.

Rules:
1. Per-dimension trend: DECLINING→REPEATED_WEAKNESS, IMPROVING→REPEATED_STRENGTH,
   STABLE→REPEATED_STRENGTH (base), INSUFFICIENT_DATA→skip.
2. Score volatility: last_score deviation from average_score > VOLATILITY_THRESHOLD
   → CONFIDENCE_DROP.
3. Session confidence: first-half vs second-half mean of ReasoningHistory entries
   (requires ≥4 entries). Drop > SESSION_DROP_THRESHOLD → CONFIDENCE_DROP on last
   entry's dominant dimension (fallback to TECHNICAL_DEPTH).
"""

from __future__ import annotations

import uuid
from statistics import mean

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_VOLATILITY_THRESHOLD = 15.0
_SESSION_DROP_THRESHOLD = 0.1
_BASE_POSITIVE_STRENGTH = 0.4

_METADATA = DetectorMetadata(
    name="TrendDetector",
    version="1.0.0",
    priority=30,
    enabled=True,
    dependencies=["ConsistencyDetector"],
)


class TrendDetector(PatternDetector):
    """Analyses score and confidence trends across the session."""

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        # V1.2 profile (ADS-06 Strategy A): one-cycle lag; None on cycle 0.
        profile_v2 = reasoner_input.candidate_profile_v2
        dim_scores = profile_v2.dimension_scores if profile_v2 is not None else {}
        history = reasoner_input.interview_memory.reasoning_history
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        trend_sigs = self._analyse_dimension_trends(dim_scores, q_idx, area)
        volatility_sigs = self._detect_score_volatility(dim_scores, q_idx, area)
        session_drop_sigs = self._detect_session_confidence_drop(history.entries, q_idx, area)

        all_sigs = filter_new_signals(trend_sigs + volatility_sigs + session_drop_sigs, store)

        matches: list[PatternMatch] = []
        pos_sigs = [s for s in trend_sigs if s.polarity == EvidencePolarity.POSITIVE]
        neg_sigs = [s for s in trend_sigs if s.polarity == EvidencePolarity.NEGATIVE]
        if pos_sigs:
            matches.append(PatternMatch(
                pattern_type=EvidenceType.REPEATED_STRENGTH,
                evidence_signals=pos_sigs,
                label=f"{len(pos_sigs)} dimension(s) improving/stable",
            ))
        if neg_sigs:
            matches.append(PatternMatch(
                pattern_type=EvidenceType.REPEATED_WEAKNESS,
                evidence_signals=neg_sigs,
                label=f"{len(neg_sigs)} dimension(s) declining",
            ))
        drop_all = volatility_sigs + session_drop_sigs
        if drop_all:
            matches.append(PatternMatch(
                pattern_type=EvidenceType.CONFIDENCE_DROP,
                evidence_signals=drop_all,
                label=f"{len(drop_all)} confidence/volatility drop(s)",
            ))

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=all_sigs,
        )

    # ------------------------------------------------------------------

    def _analyse_dimension_trends(
        self,
        dimension_scores: dict,
        q_idx: int,
        area: str,
    ) -> list[EvidenceSignal]:
        produced: list[EvidenceSignal] = []
        for dim, trace in dimension_scores.items():
            if trace.trend == Trend.INSUFFICIENT_DATA:
                continue
            if trace.trend == Trend.DECLINING:
                strength = min(0.5 + (trace.evidence_count * 0.05), 1.0)
                produced.append(self._make_signal(
                    q_idx, area, dim,
                    EvidencePolarity.NEGATIVE, EvidenceType.REPEATED_WEAKNESS, strength,
                ))
            elif trace.trend == Trend.IMPROVING:
                strength = min(0.55 + (trace.evidence_count * 0.05), 1.0)
                produced.append(self._make_signal(
                    q_idx, area, dim,
                    EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH, strength,
                ))
            elif trace.trend == Trend.STABLE:
                produced.append(self._make_signal(
                    q_idx, area, dim,
                    EvidencePolarity.POSITIVE, EvidenceType.REPEATED_STRENGTH,
                    _BASE_POSITIVE_STRENGTH,
                ))
        return produced

    def _detect_score_volatility(
        self,
        dimension_scores: dict,
        q_idx: int,
        area: str,
    ) -> list[EvidenceSignal]:
        produced: list[EvidenceSignal] = []
        for dim, trace in dimension_scores.items():
            if trace.last_score is None:
                continue
            deviation = abs(trace.last_score - trace.average_score)
            if deviation > _VOLATILITY_THRESHOLD:
                produced.append(self._make_signal(
                    q_idx, area, dim,
                    EvidencePolarity.NEGATIVE, EvidenceType.CONFIDENCE_DROP,
                    min(0.5 + deviation / 100.0, 1.0),
                ))
        return produced

    def _detect_session_confidence_drop(
        self,
        entries: list,
        q_idx: int,
        area: str,
    ) -> list[EvidenceSignal]:
        if len(entries) < 4:
            return []
        mid = len(entries) // 2
        first_half_conf = mean(e.reasoning_confidence for e in entries[:mid])
        second_half_conf = mean(e.reasoning_confidence for e in entries[mid:])
        if first_half_conf - second_half_conf <= _SESSION_DROP_THRESHOLD:
            return []
        last_entry = entries[-1]
        dim = last_entry.dominant_dimension or ProfileDimension.TECHNICAL_DEPTH
        return [self._make_signal(
            q_idx, area, dim,
            EvidencePolarity.NEGATIVE, EvidenceType.CONFIDENCE_DROP,
            min(0.6 + (first_half_conf - second_half_conf), 1.0),
        )]

    @staticmethod
    def _make_signal(
        q_idx: int,
        area: str,
        dim: ProfileDimension,
        polarity: EvidencePolarity,
        signal_type: EvidenceType,
        strength: float,
    ) -> EvidenceSignal:
        return EvidenceSignal(
            id=str(uuid.uuid4()),
            question_index=q_idx,
            question_area=area,
            dimension=dim,
            polarity=polarity,
            signal_type=signal_type,
            strength=strength,
            source=EvidenceSource.PATTERN_DETECTOR,
            timestamp_question_index=q_idx,
        )
