# services/interview_reasoner/pattern_detection/detectors/consistency_detector.py
"""ConsistencyDetector — detects signal inconsistencies within the session (ADR-034).

Algorithm (fully deterministic, O(n)):
1. Duplicate detection: group signals by (dimension, question_index, signal_type,
   polarity).  Any group with size > 1 is a duplicate cluster → emit
   REPEATED_WEAKNESS (negative) to flag recording noise.
2. Contradiction detection: for each dimension find questions where BOTH a positive
   and a negative signal exist.  Emit CONTRADICTORY_ANSWER for each such question.
3. Confidence-drop detection: compare the last two ReasoningHistory entries for the
   same dominant_dimension.  If confidence fell by > DROP_THRESHOLD emit
   CONFIDENCE_DROP signal.
"""

from __future__ import annotations

import uuid
from collections import defaultdict

from domain.contracts.reasoning.detector_context import DetectorResult
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.reasoner_input import ReasonerInput
from services.interview_reasoner.pattern_detection.base_detector import PatternDetector
from services.interview_reasoner.pattern_detection.detector_metadata import DetectorMetadata

_DUPLICATE_SIGNAL_STRENGTH = 0.4
_CONTRADICTION_SIGNAL_STRENGTH = 0.7
_CONFIDENCE_DROP_THRESHOLD = 0.15
_CONFIDENCE_DROP_SIGNAL_STRENGTH = 0.6

_METADATA = DetectorMetadata(
    name="ConsistencyDetector",
    version="1.0.0",
    priority=20,
    enabled=True,
    dependencies=["CoverageDetector"],
)


class ConsistencyDetector(PatternDetector):
    """Detects duplicates, contradictions, and confidence drops."""

    @property
    def metadata(self) -> DetectorMetadata:
        return _METADATA

    def detect(self, reasoner_input: ReasonerInput) -> DetectorResult:
        store = reasoner_input.interview_memory.evidence_store
        history = reasoner_input.interview_memory.reasoning_history
        q_idx = reasoner_input.question_index
        area = reasoner_input.current_question_area or "unknown"

        produced: list[EvidenceSignal] = []
        produced.extend(self._detect_duplicates(store.signals, q_idx, area))
        produced.extend(self._detect_contradictions(store.signals, q_idx, area))
        produced.extend(self._detect_confidence_drops(history.entries, q_idx, area))

        return DetectorResult(detector_name=_METADATA.name, evidence=produced)

    # ------------------------------------------------------------------

    def _detect_duplicates(
        self,
        signals: list[EvidenceSignal],
        q_idx: int,
        area: str,
    ) -> list[EvidenceSignal]:
        bucket: dict[tuple, list[EvidenceSignal]] = defaultdict(list)
        for sig in signals:
            key = (sig.dimension, sig.question_index, sig.signal_type, sig.polarity)
            bucket[key].append(sig)

        produced: list[EvidenceSignal] = []
        for sigs in bucket.values():
            if len(sigs) > 1:
                dim = sigs[0].dimension
                produced.append(
                    EvidenceSignal(
                        id=str(uuid.uuid4()),
                        question_index=q_idx,
                        question_area=area,
                        dimension=dim,
                        polarity=EvidencePolarity.NEGATIVE,
                        signal_type=EvidenceType.REPEATED_WEAKNESS,
                        strength=_DUPLICATE_SIGNAL_STRENGTH,
                        source=EvidenceSource.PATTERN_DETECTOR,
                        timestamp_question_index=q_idx,
                    )
                )
        return produced

    def _detect_contradictions(
        self,
        signals: list[EvidenceSignal],
        q_idx: int,
        area: str,
    ) -> list[EvidenceSignal]:
        # (dimension, question_index) → set of polarities seen
        polarity_map: dict[tuple[ProfileDimension, int], set[EvidencePolarity]] = defaultdict(set)
        for sig in signals:
            polarity_map[(sig.dimension, sig.question_index)].add(sig.polarity)

        produced: list[EvidenceSignal] = []
        for (dim, _), polarities in polarity_map.items():
            if EvidencePolarity.POSITIVE in polarities and EvidencePolarity.NEGATIVE in polarities:
                produced.append(
                    EvidenceSignal(
                        id=str(uuid.uuid4()),
                        question_index=q_idx,
                        question_area=area,
                        dimension=dim,
                        polarity=EvidencePolarity.NEGATIVE,
                        signal_type=EvidenceType.CONTRADICTORY_ANSWER,
                        strength=_CONTRADICTION_SIGNAL_STRENGTH,
                        source=EvidenceSource.PATTERN_DETECTOR,
                        timestamp_question_index=q_idx,
                    )
                )
        return produced

    def _detect_confidence_drops(
        self,
        entries: list,
        q_idx: int,
        area: str,
    ) -> list[EvidenceSignal]:
        if len(entries) < 2:
            return []

        # Find the last two entries that share the same dominant_dimension
        by_dim: dict[ProfileDimension, list] = defaultdict(list)
        for entry in entries:
            if entry.dominant_dimension is not None:
                by_dim[entry.dominant_dimension].append(entry)

        produced: list[EvidenceSignal] = []
        for dim, dim_entries in by_dim.items():
            if len(dim_entries) < 2:
                continue
            prev, last = dim_entries[-2], dim_entries[-1]
            drop = prev.reasoning_confidence - last.reasoning_confidence
            if drop > _CONFIDENCE_DROP_THRESHOLD:
                produced.append(
                    EvidenceSignal(
                        id=str(uuid.uuid4()),
                        question_index=q_idx,
                        question_area=area,
                        dimension=dim,
                        polarity=EvidencePolarity.NEGATIVE,
                        signal_type=EvidenceType.CONFIDENCE_DROP,
                        strength=min(_CONFIDENCE_DROP_SIGNAL_STRENGTH + drop, 1.0),
                        source=EvidenceSource.PATTERN_DETECTOR,
                        timestamp_question_index=q_idx,
                    )
                )
        return produced
