# services/interview_reasoner/pattern_detection/detectors/collaboration_detector.py
"""CollaborationDetector — behavioral collaboration detector (M2-7I, DET-12).

Detects collaborative behavior through interview signals:
  - Team orientation and team-first framing
  - Knowledge sharing and enabling others
  - Conflict management and constructive disagreement
  - Feedback acceptance and incorporation
  - Cross-functional collaboration across roles

Per ADR-064: dimension anchor is ProfileDimension.COMMUNICATION (V1.1 temporary mapping).
Per ADR-062: never evaluates leadership behaviors, technical correctness, grammar, or reasoning depth.

Reads LEADERSHIP_* signals (from DET-11) read-only to enrich team_orientation analysis.
MUST NOT overwrite or re-score any LEADERSHIP_* signal.

priority = 110
dependencies = ["LeadershipDetector"]

Signals emitted:
  COLLABORATION_STRONG    — strong multi-faceted collaboration pattern
  COLLABORATION_EFFECTIVE — solid collaboration indicators present
  COLLABORATION_DEFICIT   — individualistic or conflict-avoidant pattern

Deterministic; O(n); no LLM; no external services.
"""

from __future__ import annotations

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.collaboration.analyzer import (
    CollaborationAnalyzer,
)
from services.interview_reasoner.pattern_detection.detectors.collaboration.scorer import (
    CollaborationScorer,
    CollaborationVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.collaboration.signal_factory import (
    CollaborationSignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="CollaborationDetector",
    version="1.0.0",
    priority=110,
    enabled=True,
    dependencies=["LeadershipDetector"],
)

_MIN_BEHAVIORAL_SIGNALS = 3


class CollaborationDetector(PatternDetector):
    """Detect collaboration patterns from behavioral EvidenceStore signals."""

    def __init__(self) -> None:
        self._analyzer = CollaborationAnalyzer()
        self._scorer = CollaborationScorer()
        self._factory = CollaborationSignalFactory()

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

        if verdict == CollaborationVerdict.NEUTRAL:
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
                    f"Collaboration[{verdict.value}]: "
                    f"ratio={stats.collaboration_ratio:.2f}, "
                    f"conflict_res={stats.conflict_resolution_ratio:.2f}"
                ),
            ))

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
        )
