# services/interview_reasoner/pattern_detection/detectors/adaptability_detector.py
"""AdaptabilityDetector — behavioral adaptability detector (M2-7J, DET-13).

Detects candidate adaptability through interview behavioral signals:
  - Recovery after mistakes (INSTABILITY → GROWTH within window)
  - Flexibility under pressure (CROSS_AREA_CONSISTENT multi-area)
  - Learning speed and context switching
  - Problem reframing (CROSS_AREA_CONTRADICTORY positively resolved)

Per ADR-065: recovery window = 3 question indices.
Per ADR-062: never evaluates leadership, collaboration, communication, technical correctness.

priority = 120
dependencies = ["CollaborationDetector"]

Signals emitted:
  ADAPTABILITY_HIGH     — strong recovery and flexibility demonstrated
  ADAPTABILITY_MODERATE — adequate adaptability present
  ADAPTABILITY_LOW      — rigidity pattern; low recovery rate

Deterministic; O(n); no LLM; no external services.
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.adaptability.analyzer import (
    AdaptabilityAnalyzer,
)
from services.interview_reasoner.pattern_detection.detectors.adaptability.scorer import (
    AdaptabilityScorer,
    AdaptabilityVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.adaptability.signal_factory import (
    AdaptabilitySignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="AdaptabilityDetector",
    version="1.0.0",
    priority=120,
    enabled=True,
    dependencies=["CollaborationDetector"],
)

_MIN_BEHAVIORAL_SIGNALS = 2


class AdaptabilityDetector(PatternDetector):
    """Detect adaptability patterns from behavioral EvidenceStore signals."""

    def __init__(self) -> None:
        self._analyzer = AdaptabilityAnalyzer()
        self._scorer = AdaptabilityScorer()
        self._factory = AdaptabilitySignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        stats = self._analyzer.analyze(store.signals)

        if stats.total_behavioral_signals < _MIN_BEHAVIORAL_SIGNALS:
            return DetectorResult(detector_name=_METADATA.name)

        verdict = self._scorer.score(stats)

        if verdict == AdaptabilityVerdict.NEUTRAL:
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
                    f"Adaptability[{verdict.value}]: "
                    f"ratio={stats.adaptability_ratio:.2f}, "
                    f"recovery={stats.recovery_count}/{stats.total_instability_events}, "
                    f"rigidity={stats.rigidity_count}"
                ),
            ))

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
        )
