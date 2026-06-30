# services/interview_reasoner/pattern_detection/detectors/trend_detector.py
"""TrendDetector — analyses score and confidence trends across the session (ADR-034).

Algorithm (fully deterministic, O(n)):
Sources used: DimensionTrace (from CandidateProfile), ReasoningHistory,
              EvidenceStore.  No LLM calls.

Rules:
1. For each ProfileDimension with a DimensionTrace:
   - Trend.DECLINING  → emit REPEATED_WEAKNESS with strength proportional to evidence_count.
   - Trend.IMPROVING  → emit REPEATED_STRENGTH.
   - Trend.STABLE     → emit REPEATED_STRENGTH at low strength (baseline positive signal).
   - Trend.INSUFFICIENT_DATA → skip (not enough data; CoverageDetector handles absence).
2. Score volatility: if a dimension's last_score deviates from average_score by more than
   VOLATILITY_THRESHOLD, emit CONFIDENCE_DROP to flag instability.
3. Overall session trend (from ReasoningHistory): compare average reasoning_confidence
   of the first half vs second half of entries.  If the drop exceeds SESSION_DROP_THRESHOLD
   emit one aggregate CONFIDENCE_DROP on the dominant dimension of the most recent entry.
"""

from __future__ import annotations

import uuid
from statistics import mean

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata

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
        profile = reasoner_input.interview_memory.candidate_profile
        history = reasoner_input.interview_memory.reasoning_history
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        produced: list[EvidenceSignal] = []
        produced.extend(self._analyse_dimension_trends(profile.dimension_scores, q_idx, area))
        produced.extend(self._detect_score_volatility(profile.dimension_scores, q_idx, area))
        produced.extend(self._detect_session_confidence_drop(history.entries, q_idx, area))

        return DetectorResult(detector_name=_METADATA.name, evidence=produced)

    # ------------------------------------------------------------------

    def _analyse_dimension_trends(
        self,
        dimension_scores: dict[ProfileDimension, object],
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
        dimension_scores: dict[ProfileDimension, object],
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
