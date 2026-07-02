# domain/contracts/observation/observation_status.py
# ADR-017: ObservationStore lifecycle & temporal semantics — logical states

from enum import Enum


class ObservationStatus(str, Enum):
    """Lifecycle state of an Observation within the ObservationStore.

    Transition rules (ADR-017):
        ACTIVE   — newly appended; eligible for FeatureEngine consumption.
        DECAYED  — TTL has elapsed; weight is reduced but entry is retained for
                   audit and replay (ADR-021).
        EXPIRED  — beyond hard expiry boundary; excluded from feature
                   computation but retained for SessionHistory archival.
        SUPERSEDED — a later Observation of the same type + source +
                     question_index has been appended; this entry is logically
                     replaced (deduplication rule, ADR-017 Section D).

    Only ObservationStore transitions status — no external writer permitted.
    """

    ACTIVE = "active"
    DECAYED = "decayed"
    EXPIRED = "expired"
    SUPERSEDED = "superseded"
