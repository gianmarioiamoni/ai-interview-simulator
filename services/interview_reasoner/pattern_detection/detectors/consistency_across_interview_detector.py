# services/interview_reasoner/pattern_detection/detectors/consistency_across_interview_detector.py
"""ConsistencyAcrossInterviewDetector — cross-interview consistency detector (M2-7D, DET-09).

Evaluates long-term consistency across the entire interview:
  - Contradictions appearing across question areas within the same dimension
  - Repeated strengths across distinct areas
  - Stable cross-area reasoning
  - Persistent improvement or regression

Does NOT inspect only the latest answer — uses full EvidenceStore.

priority = 80  (after BehavioralPatternDetector at 70)
dependencies = ["BehavioralPatternDetector"]

Signals emitted (per dimension):
  CROSS_AREA_CONTRADICTORY — opposite polarity patterns in same dimension across areas
  CROSS_AREA_CONSISTENT    — consistent polarity across areas in same dimension

PatternMatch types:
  CROSS_AREA_CONTRADICTORY → same
  CROSS_AREA_CONSISTENT    → same

Guard: fires only when ≥ 2 distinct question areas exist for the same dimension.

Deterministic; O(n); no LLM; no NLP.

Future V1.2:
  Observation type: ConsistencyObservation
  ProfileFeature: CrossDomainConsistencyFeature
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.analyzer import (
    ConsistencyHistoryAnalyzer,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.scorer import (
    ConsistencyScorer,
    ConsistencyVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.consistency_across_interview.signal_factory import (
    ConsistencySignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="ConsistencyAcrossInterviewDetector",
    version="1.0.0",
    priority=80,
    enabled=True,
    dependencies=["BehavioralPatternDetector"],
)


class ConsistencyAcrossInterviewDetector(PatternDetector):
    """Detect cross-area consistency/contradictions across the full interview session."""

    def __init__(self) -> None:
        self._analyzer = ConsistencyHistoryAnalyzer()
        self._scorer = ConsistencyScorer()
        self._factory = ConsistencySignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        cross_results = self._analyzer.analyze(store.signals)

        candidates = []
        matches: list[PatternMatch] = []

        for result in cross_results:
            verdict = self._scorer.score(result)
            if verdict == ConsistencyVerdict.NEUTRAL:
                continue

            sig = self._factory.make_signal(verdict, result, q_idx, area)
            if sig is None:
                continue

            label = self._build_label(verdict, result)
            matches.append(PatternMatch(
                pattern_type=sig.signal_type,
                evidence_signals=[sig],
                label=label,
            ))
            candidates.append(sig)

        if not matches:
            return DetectorResult(detector_name=_METADATA.name)

        new_signals = filter_new_signals(candidates, store)

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
        )

    def _build_label(self, verdict: ConsistencyVerdict, result) -> str:
        dim = result.dimension.value
        delta = result.max_ratio_delta
        if verdict == ConsistencyVerdict.CONTRADICTORY:
            a, b = result.contradictory_areas
            return f"cross_area_contradiction: {dim} [{a} vs {b}] delta={delta:.2f}"
        return f"cross_area_consistent: {dim} delta={delta:.2f}"
