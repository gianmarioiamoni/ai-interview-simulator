# services/interview_reasoner/pattern_detection/detectors/coverage_detector.py
"""CoverageDetector — analyses which ProfileDimensions have been observed
and flags under-covered or completely absent dimensions (ADR-034).

Algorithm (fully deterministic, O(n)):
1. Count evidence signals per dimension from EvidenceStore.
2. Compare against all ProfileDimension enum members.
3. Emit MISSING_EVIDENCE signal for every dimension with zero evidence.
4. Emit REPEATED_WEAKNESS signal for every dimension below the low-coverage
   threshold (< LOW_COVERAGE_THRESHOLD evidence signals), excluding absent ones.
   Priority: dimensions where last DimensionTrace.trend is DECLINING.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from domain.contracts.reasoning.trend import Trend
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals
from infrastructure.config.settings import settings as _settings

_LOW_COVERAGE_THRESHOLD = 2
_COVERAGE_SIGNAL_STRENGTH = 0.6
_LOW_COVERAGE_SIGNAL_STRENGTH = 0.5

_METADATA = DetectorMetadata(
    name="CoverageDetector",
    version="1.0.0",
    priority=10,
    enabled=True,
    dependencies=[],
)


class CoverageDetector(PatternDetector):
    """Detects uncovered and under-covered ProfileDimensions."""

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        # Threshold guard: stay silent until enough questions have been answered.
        questions_answered = reasoner_input.interview_memory.session_metrics.questions_answered
        min_q = _settings.reasoner_coverage_min_questions
        if questions_answered < min_q:
            return DetectorResult(detector_name=_METADATA.name)

        store = reasoner_input.interview_memory.evidence_store
        # V1.2 profile (ADS-06 Strategy A): one-cycle lag is intentional and
        # below the min_evidence_for_trend threshold. None on cycle 0.
        profile = reasoner_input.candidate_profile_v2
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        evidence_per_dim: dict[ProfileDimension, int] = {
            dim: 0 for dim in ProfileDimension
        }
        for sig in store.signals:
            evidence_per_dim[sig.dimension] += 1

        missing_sigs: list[EvidenceSignal] = []
        weak_sigs: list[EvidenceSignal] = []

        for dim in ProfileDimension:
            count = evidence_per_dim[dim]
            dim_trace = profile.dimension_scores.get(dim) if profile is not None else None

            if count == 0:
                missing_sigs.append(
                    EvidenceSignal(
                        id=str(uuid.uuid4()),
                        question_index=q_idx,
                        question_area=area,
                        dimension=dim,
                        polarity=EvidencePolarity.NEGATIVE,
                        signal_type=EvidenceType.MISSING_EVIDENCE,
                        strength=_COVERAGE_SIGNAL_STRENGTH,
                        source=EvidenceSource.PATTERN_DETECTOR,
                        timestamp_question_index=q_idx,
                    )
                )
            elif count < _LOW_COVERAGE_THRESHOLD:
                strength = _LOW_COVERAGE_SIGNAL_STRENGTH
                if dim_trace is not None and dim_trace.trend == Trend.DECLINING:
                    strength = min(strength + 0.15, 1.0)
                weak_sigs.append(
                    EvidenceSignal(
                        id=str(uuid.uuid4()),
                        question_index=q_idx,
                        question_area=area,
                        dimension=dim,
                        polarity=EvidencePolarity.NEGATIVE,
                        signal_type=EvidenceType.REPEATED_WEAKNESS,
                        strength=strength,
                        source=EvidenceSource.PATTERN_DETECTOR,
                        timestamp_question_index=q_idx,
                    )
                )

        all_signals = missing_sigs + weak_sigs
        # Idempotency: do not re-emit structurally identical signals.
        all_signals = filter_new_signals(all_signals, store)
        # Re-partition after filtering (matches should only reference surviving signals)
        surviving_missing = [s for s in all_signals if s.signal_type == EvidenceType.MISSING_EVIDENCE]
        surviving_weak = [s for s in all_signals if s.signal_type == EvidenceType.REPEATED_WEAKNESS]

        matches = []
        if surviving_missing:
            matches.append(PatternMatch(
                pattern_type=EvidenceType.MISSING_EVIDENCE,
                evidence_signals=surviving_missing,
                label=f"{len(surviving_missing)} dimension(s) with no evidence",
            ))
        if surviving_weak:
            matches.append(PatternMatch(
                pattern_type=EvidenceType.REPEATED_WEAKNESS,
                evidence_signals=surviving_weak,
                label=f"{len(surviving_weak)} dimension(s) under coverage threshold",
            ))

        warnings: list[str] = []
        if len(all_signals) == len(list(ProfileDimension)):
            warnings.append("All dimensions lack sufficient coverage.")

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=all_signals,
            warnings=warnings,
        )
