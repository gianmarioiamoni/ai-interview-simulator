# domain/contracts/observation/extraction/observation_rule_priority.py
# ADR-016: Rule ordering — deterministic priority model

from enum import IntEnum


class ObservationRulePriority(IntEnum):
    """Execution priority for ObservationRule instances.

    Lower integer value = higher priority (executed first).

    Rules are applied in strict ascending priority order within the extractor.
    Within the same priority level, tie-breaking is by rule_id lexicographic
    order to guarantee determinism (ADR-016 Section F).

    CRITICAL (10)  — Safety / correctness gates; must run before all others.
    HIGH (20)      — Primary behavioral detectors (DET-11/12/13, ADR-066).
    NORMAL (50)    — Standard evidence signal rules.
    LOW (80)       — Supplementary / enrichment rules.
    FALLBACK (100) — Default catch-all rules; run last.
    """

    CRITICAL = 10
    HIGH = 20
    NORMAL = 50
    LOW = 80
    FALLBACK = 100
