# domain/contracts/observation/observation_origin.py
# ADR-016: Observation schema — provenance model

from enum import Enum


class ObservationOrigin(str, Enum):
    """Provenance of an Observation — which subsystem produced it.

    Immutable registry (ADR-016). New origins require a documentation ADR;
    no origin may be removed without deprecation.

    EVALUATION       — produced from EvaluationResult signals (primary path).
    EVIDENCE_SIGNAL  — produced directly from EvidenceSignal (canonical flow,
                       ADR-016 Section A-2).
    PATTERN_DETECTOR — produced by a behavioural pattern detector
                       (DET-11/12/13, ADR-066).
    REPLAY           — re-constructed from SessionHistory by ReplayUpdater
                       (ADR-021, ADR-022); read-only origin; never emitted at
                       runtime.
    CALIBRATION      — injected by CalibrationUpdater for baseline anchoring
                       (ADR-024); never emitted in standard session flow.
    """

    EVALUATION = "evaluation"
    EVIDENCE_SIGNAL = "evidence_signal"
    PATTERN_DETECTOR = "pattern_detector"
    REPLAY = "replay"
    CALIBRATION = "calibration"
