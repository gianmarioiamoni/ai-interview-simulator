# domain/contracts/narrative/narrative_insight_type.py
# ADR-023 Section C — NarrativeInsightType taxonomy (frozen)

from enum import Enum


class NarrativeInsightType(str, Enum):
    """Atomic finding types for NarrativeInsight (ADR-023 §C).

    Each insight traces to exactly one ProfileFeature (invariant C-02).
    """

    STRENGTH_SIGNAL = "strength_signal"
    RISK_SIGNAL = "risk_signal"
    GROWTH_OPPORTUNITY = "growth_opportunity"
    ANOMALY = "anomaly"
