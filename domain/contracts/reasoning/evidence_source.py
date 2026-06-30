# domain/contracts/reasoning/evidence_source.py

from enum import Enum


class EvidenceSource(str, Enum):
    EVALUATION = "evaluation"
    FEEDBACK = "feedback"
    PATTERN_DETECTOR = "pattern_detector"
    # Reserved for V1.2 — cross-source combined signals (ADR-039).
    # Never emitted in V1.1 M2.
    DERIVED = "derived"
