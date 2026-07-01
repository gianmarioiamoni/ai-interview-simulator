# services/interview_reasoner/pattern_detection/detectors/leadership_detector.py
"""LeadershipDetector — behavioral leadership detector (M2-7H, DET-11).

Detects leadership potential through interview behavior:
  - Ownership and accountability language
  - Initiative and proactive problem identification
  - Accountability / recovery after instability
  - Mentoring attitude (cross-area knowledge sharing patterns)
  - Strategic thinking (consistent multi-area behavioral signals)

Per ADR-063: dimension anchor is ProfileDimension.PROBLEM_SOLVING (V1.1 temporary mapping).
Per ADR-062: never evaluates communication quality, technical correctness, or engineering judgment.

priority = 100
dependencies = ["ConsistencyAcrossInterviewDetector"]

Signals emitted:
  LEADERSHIP_STRONG   — strong multi-dimension leadership signals
  LEADERSHIP_EMERGING — early leadership pattern detected
  LEADERSHIP_ABSENT   — behavioral data present but no leadership signals

Deterministic; O(n); no LLM; no external services.
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.leadership.analyzer import (
    LeadershipAnalyzer,
)
from services.interview_reasoner.pattern_detection.detectors.leadership.scorer import (
    LeadershipScorer,
    LeadershipVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.leadership.signal_factory import (
    LeadershipSignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="LeadershipDetector",
    version="1.0.0",
    priority=100,
    enabled=True,
    dependencies=["ConsistencyAcrossInterviewDetector"],
)

# Minimum behavioral signals before firing the detector.
_MIN_BEHAVIORAL_SIGNALS = 3


class LeadershipDetector(PatternDetector):
    """Detect leadership potential from behavioral EvidenceStore signals."""

    def __init__(self) -> None:
        self._analyzer = LeadershipAnalyzer()
        self._scorer = LeadershipScorer()
        self._factory = LeadershipSignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        stats = self._analyzer.analyze(store.signals)

        # Guard: insufficient behavioral signals → return empty result.
        if stats.total_behavioral_signals < _MIN_BEHAVIORAL_SIGNALS:
            return DetectorResult(detector_name=_METADATA.name)

        verdict = self._scorer.score(stats)

        # NEUTRAL → no signal, no matches.
        if verdict == LeadershipVerdict.NEUTRAL:
            return DetectorResult(detector_name=_METADATA.name)

        signal = self._factory.create(verdict, stats, q_idx, area)
        candidates = [signal] if signal is not None else []
        new_signals = filter_new_signals(candidates, store)

        matches: list[PatternMatch] = []
        if signal is not None:
            matches.append(PatternMatch(
                pattern_type=signal.signal_type,
                evidence_signals=[signal],
                label=(
                    f"Leadership[{verdict.value}]: "
                    f"ratio={stats.leadership_ratio:.2f}, "
                    f"dims={stats.active_dimension_count}"
                ),
            ))

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
        )
