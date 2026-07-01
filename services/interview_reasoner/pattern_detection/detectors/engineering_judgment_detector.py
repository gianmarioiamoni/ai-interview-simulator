# services/interview_reasoner/pattern_detection/detectors/engineering_judgment_detector.py
"""EngineeringJudgmentDetector — engineering maturity detector (M2-7C, DET-06).

Detects engineering maturity based on:
  - Trade-off reasoning signals
  - Production / operational thinking signals
  - Scalability and maintainability signals
  - Risk and decision justification signals

All evidence is derived from ENGINEERING_JUDGMENT dimension signals already
present in the EvidenceStore — never technical correctness, communication, or
knowledge depth.

priority = 50  (after ReasoningDepthDetector at 40)
dependencies = ["ReasoningDepthDetector"]

Signals emitted:
  ENGINEERING_JUDGMENT_HIGH — strong engineering judgment demonstrated
  ENGINEERING_JUDGMENT_LOW  — shallow or absent engineering judgment

Also emits KNOWLEDGE_GAP when judgment dimension has no evaluation evidence
after the coverage threshold.

Deterministic; O(n); no LLM; no NLP.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.analyzer import (
    EngineeringJudgmentAnalyzer,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.scorer import (
    EngineeringJudgmentScorer,
    JudgmentVerdict,
)
from services.interview_reasoner.pattern_detection.detectors.engineering_judgment.signal_factory import (
    EngineeringJudgmentSignalFactory,
)
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

_METADATA = DetectorMetadata(
    name="EngineeringJudgmentDetector",
    version="1.0.0",
    priority=50,
    enabled=True,
    dependencies=["ReasoningDepthDetector"],
)

# Minimum questions answered before firing the missing-judgment gap signal.
_MIN_QUESTIONS_FOR_GAP = 2


class EngineeringJudgmentDetector(PatternDetector):
    """Detect engineering maturity via judgment signal ratio on ENGINEERING_JUDGMENT dimension."""

    def __init__(self) -> None:
        self._analyzer = EngineeringJudgmentAnalyzer()
        self._scorer = EngineeringJudgmentScorer()
        self._factory = EngineeringJudgmentSignalFactory()

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"
        questions_answered = reasoner_input.interview_memory.session_metrics.questions_answered

        stats = self._analyzer.analyze(store.signals)
        verdict = self._scorer.score(stats)

        candidates = []
        matches: list[PatternMatch] = []
        warnings: list[str] = []

        sig = self._factory.make_signal(verdict, stats, q_idx, area)
        if sig is not None:
            candidates.append(sig)
            matches.append(PatternMatch(
                pattern_type=sig.signal_type,
                evidence_signals=[sig],
                label=(
                    f"engineering_judgment: ratio={stats.judgment_ratio:.2f} "
                    f"({stats.positive_count}+/{stats.negative_count}-)"
                ),
            ))

        # Emit KNOWLEDGE_GAP when dimension has no evaluation evidence after threshold.
        gap_sig = self._maybe_gap_signal(stats, questions_answered, q_idx, area)
        if gap_sig is not None:
            candidates.append(gap_sig)
            matches.append(PatternMatch(
                pattern_type=EvidenceType.KNOWLEDGE_GAP,
                evidence_signals=[gap_sig],
                label="engineering_judgment: no evaluation evidence observed",
            ))

        new_signals = filter_new_signals(candidates, store)

        if not matches:
            return DetectorResult(detector_name=_METADATA.name, warnings=warnings)

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
            warnings=warnings,
        )

    def _maybe_gap_signal(
        self,
        stats,
        questions_answered: int,
        q_idx: int,
        area: str,
    ) -> EvidenceSignal | None:
        """Emit a KNOWLEDGE_GAP signal when the dimension has no evidence after threshold."""
        if stats.evaluation_signal_count > 0:
            return None
        if questions_answered < _MIN_QUESTIONS_FOR_GAP:
            return None
        return EvidenceSignal(
            id=str(uuid.uuid4()),
            question_index=q_idx,
            question_area=area,
            dimension=ProfileDimension.ENGINEERING_JUDGMENT,
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.KNOWLEDGE_GAP,
            strength=0.5,
            source=EvidenceSource.PATTERN_DETECTOR,
            timestamp_question_index=q_idx,
        )
