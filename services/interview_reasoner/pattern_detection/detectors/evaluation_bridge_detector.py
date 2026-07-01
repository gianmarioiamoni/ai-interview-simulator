# services/interview_reasoner/pattern_detection/detectors/evaluation_bridge_detector.py
"""EvaluationBridgeDetector — bridges evaluation-origin EvidenceSignals into
the PatternDetection pipeline so that ReasonerService can produce
FollowUpRecommendations from them (M2-6A, P0 fix).

Architecture:
  Evaluation → EvidenceStore ← (evaluation pipeline writes)
                             ↓
             EvaluationBridgeDetector reads & converts to PatternMatch
                             ↓
              ReasonerService aggregates detected_types
                             ↓
              _build_follow_up_recommendation checks _FOLLOW_UP_TRIGGER_TYPES

ReasonerService is unchanged.  No direct EvidenceStore inspection is added
to ReasonerService.  Architectural contract (ADR-034) preserved.

Responsibilities:
- Read existing signals from EvidenceStore (read-only).
- Identify evaluation-origin signals whose type is in BRIDGEABLE_TYPES.
- Convert them to PatternMatch entries so ReasonerService can see them.
- Emit a single derived EvidenceSignal per (type, dimension, question)
  identity only when no equivalent signal already exists (idempotency).
- Deterministic; O(n); no LLM; no mutation.

priority = 5 (runs before CoverageDetector at 10).
"""

from __future__ import annotations

import uuid

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata
from services.interview_reasoner.pattern_detection.signal_idempotency import filter_new_signals

# Evaluation-origin signal types that the pipeline should react to.
BRIDGEABLE_TYPES: frozenset[EvidenceType] = frozenset({
    EvidenceType.KNOWLEDGE_GAP,
    EvidenceType.SHALLOW_ANSWER,
    EvidenceType.REASONING_GAP,
})

_METADATA = DetectorMetadata(
    name="EvaluationBridgeDetector",
    version="1.0.0",
    priority=5,
    enabled=True,
    dependencies=[],
)


class EvaluationBridgeDetector(PatternDetector):
    """Promotes evaluation-origin signals into the pattern detection pipeline."""

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        # Group existing evaluation-origin signals by type for PatternMatch.
        bridgeable: dict[EvidenceType, list[EvidenceSignal]] = {}
        for sig in store.signals:
            if sig.signal_type in BRIDGEABLE_TYPES and sig.source == EvidenceSource.EVALUATION:
                bridgeable.setdefault(sig.signal_type, []).append(sig)

        if not bridgeable:
            return DetectorResult(detector_name=_METADATA.name)

        matches: list[PatternMatch] = []
        candidate_derived: list[EvidenceSignal] = []

        for etype, sigs in bridgeable.items():
            matches.append(PatternMatch(
                pattern_type=etype,
                evidence_signals=sigs,
                label=f"{len(sigs)} evaluation-origin {etype.value} signal(s)",
            ))
            # Derive one consolidated PATTERN_DETECTOR signal per
            # (type, dimension) pair so ReasonerService can use it for
            # recommendations.  Idempotency prevents duplicates on re-runs.
            dims_seen: set = set()
            for sig in sigs:
                if sig.dimension not in dims_seen:
                    dims_seen.add(sig.dimension)
                    candidate_derived.append(EvidenceSignal(
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

        # Idempotency: skip signals whose identity already exists in store.
        new_signals = filter_new_signals(candidate_derived, store)

        return DetectorResult(
            detector_name=_METADATA.name,
            matches=matches,
            generated_signals=new_signals,
        )
