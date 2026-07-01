# services/interview_reasoner/pattern_detection/detectors/behavioral_pattern_detector.py
"""BehavioralPatternDetector — cross-answer behavioral pattern detector (M2-7D, DET-08).

Detects behavioral characteristics emerging across multiple answers:
  - Confidence evolution (growing, declining, plateau)
  - Hesitation reduction over time
  - Learning during interview (improving answer quality)
  - Consistency of behavioral attitude
  - Openness to feedback / adaptability
  - Answer stability

Does NOT evaluate:
  - Technical correctness
  - Knowledge depth
  - Communication quality
  - Engineering judgment

priority = 70  (after CommunicationDetector at 60)
dependencies = ["CommunicationDetector"]

Signals emitted:
  BEHAVIORAL_GROWTH      — candidate growing in confidence/competence
  BEHAVIORAL_INSTABILITY — erratic or inconsistent behavioral patterns
  BEHAVIORAL_PLATEAU     — stable but not improving

PatternMatch types:
  BEHAVIORAL_GROWTH      → same
  BEHAVIORAL_INSTABILITY → same
  BEHAVIORAL_PLATEAU     → same

Guard: requires ≥ MIN_ENTRIES (3) reasoning history entries before firing.

Deterministic; O(n); no LLM; no NLP.

Future V1.2:
  Observation type: BehavioralObservation
  ProfileFeature: BehavioralPatternFeature
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.analyzer import (
    BehaviorObservationExtractor,
)
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.scorer import (
    BehaviorPatternScorer,
    BehaviorVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.behavioral_pattern.signal_factory import (
    BehaviorSignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="BehavioralPatternDetector",
    version="1.0.0",
    priority=70,
    enabled=True,
    dependencies=["CommunicationDetector"],
)


class BehavioralPatternDetector(PatternDetector):
    """Detect behavioral patterns from ReasoningHistory trajectory."""

    def __init__(self) -> None:
        self._extractor = BehaviorObservationExtractor()
        self._scorer = BehaviorPatternScorer()
        self._factory = BehaviorSignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        history = reasoner_input.interview_memory.reasoning_history
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        stats = self._extractor.analyze(history.entries)
        verdict = self._scorer.score(stats)

        if verdict == BehaviorVerdict.NEUTRAL:
            return DetectorResult(detector_name=_METADATA.name)

        sig = self._factory.make_signal(verdict, stats, q_idx, area)
        if sig is None:
            return DetectorResult(detector_name=_METADATA.name)

        match = PatternMatch(
            pattern_type=sig.signal_type,
            evidence_signals=[sig],
            label=(
                f"behavioral: {verdict.value} "
                f"(conf_trend={stats.confidence_trend:+.2f}, "
                f"pos_ratio={stats.positive_ratio:.2f}, "
                f"variance={stats.variance_score:.2f})"
            ),
        )

        new_signals = filter_new_signals([sig], store)

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=[match],
            generated_signals=new_signals,
        )
