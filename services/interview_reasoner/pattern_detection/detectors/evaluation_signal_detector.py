# services/interview_reasoner/pattern_detection/detectors/evaluation_signal_detector.py
"""EvaluationSignalDetector — sliding-window bridge of evaluation-origin signals (M2-7B).

Successor to EvaluationBridgeDetector (ADR-052).

Key difference from EvaluationBridgeDetector:
  Only signals from the last `window` answered question indices are bridged
  into active PatternMatches.  Older signals remain in EvidenceStore but no
  longer generate derived PATTERN_DETECTOR signals, preventing stale coaching.

Architecture:
  Evaluation Pipeline  →  EvidenceStore  (writes EVALUATION-source signals)
                               ↓
        EvaluationSignalDetector (reads, filters by sliding window)
                               ↓
        PatternMatch entries  +  derived EvidenceSignals (idempotent)
                               ↓
        ReasonerService aggregates detected_types → follow-up / navigation

Contracts:
  priority = 5  (before CoverageDetector)
  dependencies = []
  O(n) in EvidenceStore signals
  Deterministic; no LLM; no mutation.
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from infrastructure.config.settings import settings as _settings
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

# Evaluation-origin types that should activate follow-up / navigation logic.
BRIDGEABLE_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.KNOWLEDGE_GAP,
    EvidenceType.SHALLOW_ANSWER,
    EvidenceType.REASONING_GAP,
})

_METADATA = DetectorMetadata(
    name="EvaluationSignalDetector",
    version="1.0.0",
    priority=5,
    enabled=True,
    dependencies=[],
)


class EvaluationSignalDetector(PatternDetector):
    """Bridges recent evaluation signals into the pattern detection pipeline.

    Implements the sliding-window strategy from ADR-052: only signals whose
    ``question_index`` falls within the last ``reasoner_bridge_window``
    answered question indices are eligible for bridging.
    """

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"
        window = _settings.reasoner_bridge_window

        # Collect the last `window` distinct question indices with evaluation signals.
        window_indices = self._recent_question_indices(store.signals, window, q_idx)
        if not window_indices:
            return DetectorResult(detector_name=_METADATA.name)

        # Group in-window evaluation-origin signals by type.
        bridgeable: dict[EvidenceType, list[EvidenceSignal]] = {}
        for sig in store.signals:
            if (
                sig.signal_type in BRIDGEABLE_TYPES
                and sig.source == EvidenceSource.EVALUATION
                and sig.question_index in window_indices
            ):
                bridgeable.setdefault(sig.signal_type, []).append(sig)

        if not bridgeable:
            return DetectorResult(detector_name=_METADATA.name)

        matches: list[PatternMatch] = []
        candidates: list[EvidenceSignal] = []

        for etype, sigs in bridgeable.items():
            matches.append(PatternMatch(
                pattern_type=etype,
                evidence_signals=sigs,
                label=f"{len(sigs)} recent {etype.value} signal(s) (window={window})",
            ))
            # One derived PATTERN_DETECTOR signal per (type, dimension) pair.
            dims_seen: set = set()
            for sig in sigs:
                if sig.dimension not in dims_seen:
                    dims_seen.add(sig.dimension)
                    candidates.append(EvidenceSignal(
                        id=str(uuid.uuid4()),
                        question_index=q_idx,
                        question_area=area,
                        dimension=sig.dimension,
                        polarity=sig.polarity,
                        signal_type=etype,
                        strength=sig.strength,
                        source=EvidenceSource.PATTERN_DETECTOR,
                        timestamp_question_index=q_idx,
                    ))

        new_signals = filter_new_signals(candidates, store)
        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
        )

    @staticmethod
    def _recent_question_indices(
        signals: list[EvidenceSignal],
        window: int,
        current_q_idx: int,
    ) -> frozenset[int]:
        """Return the set of question indices eligible for bridging.

        An index is eligible when it falls within the sliding window:
            [current_q_idx - window + 1, current_q_idx]

        O(n) single pass.
        """
        min_idx = current_q_idx - window + 1
        return frozenset(
            sig.question_index
            for sig in signals
            if sig.source == EvidenceSource.EVALUATION
            and min_idx <= sig.question_index <= current_q_idx
        )
