# services/interview_reasoner/pattern_detection/detectors/communication_detector.py
"""CommunicationDetector — communication quality detector (M2-7C, DET-07).

Evaluates communication quality based ONLY on:
  - Logical flow and clarity (COMMUNICATION dimension signals)
  - Conciseness and organization
  - Ability to explain technical concepts (COMMUNICATION dim strength)

Does NOT evaluate:
  - Grammar or English level
  - Technical correctness
  - Knowledge depth

priority = 60  (after EngineeringJudgmentDetector at 50)
dependencies = ["ConsistencyDetector"]

Signals emitted:
  COMMUNICATION_CLEAR        — consistent clear communication
  COMMUNICATION_WEAK         — persistent communication weakness
  COMMUNICATION_INCONSISTENT — inconsistent communication signals

PatternMatch types:
  COMMUNICATION_CLEAR   → COMMUNICATION_CLEAR signal
  COMMUNICATION_GAP     → COMMUNICATION_WEAK signal
  CONTRADICTORY_ANSWER  → COMMUNICATION_INCONSISTENT signal

Guard: fires only when COMMUNICATION dimension has ≥ 2 evidence signals.

Deterministic; O(n); no LLM; no NLP.
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.communication.analyzer import (
    CommunicationObservationExtractor,
)
from services.interview_reasoner.pattern_detection.detectors.communication.scorer import (
    CommunicationScorer,
    CommunicationVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.communication.signal_factory import (
    CommunicationSignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="CommunicationDetector",
    version="1.0.0",
    priority=60,
    enabled=True,
    dependencies=["ConsistencyDetector"],
)

# Map verdict → PatternMatch pattern_type (TDS DET-07 contract).
_VERDICT_PATTERN_TYPE: dict[CommunicationVerdict, EvidenceType] = {
    CommunicationVerdict.CLEAR: EvidenceType.COMMUNICATION_CLEAR,
    CommunicationVerdict.WEAK: EvidenceType.COMMUNICATION_GAP,
    CommunicationVerdict.INCONSISTENT: EvidenceType.CONTRADICTORY_ANSWER,
}


class CommunicationDetector(PatternDetector):
    """Detect communication quality via signal ratio on COMMUNICATION dimension."""

    def __init__(self) -> None:
        self._extractor = CommunicationObservationExtractor()
        self._scorer = CommunicationScorer()
        self._factory = CommunicationSignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        stats = self._extractor.analyze(store.signals)
        verdict = self._scorer.score(stats)

        if verdict == CommunicationVerdict.NEUTRAL:
            return DetectorResult(detector_name=_METADATA.name)

        sig = self._factory.make_signal(verdict, stats, q_idx, area)
        if sig is None:
            return DetectorResult(detector_name=_METADATA.name)

        pattern_type = _VERDICT_PATTERN_TYPE[verdict]
        match = PatternMatch(
            pattern_type=pattern_type,
            evidence_signals=[sig],
            label=(
                f"communication: {verdict.value} "
                f"(+{stats.positive_count}/-{stats.negative_count}"
                f"/~{stats.inconsistent_count})"
            ),
        )

        new_signals = filter_new_signals([sig], store)

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=[match],
            generated_signals=new_signals,
        )
