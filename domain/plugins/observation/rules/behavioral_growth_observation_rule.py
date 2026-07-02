# domain/plugins/observation/rules/behavioral_growth_observation_rule.py

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType

_BEHAVIORAL_SIGNAL_TYPES = frozenset({
    EvidenceType.BEHAVIORAL_GROWTH,
    EvidenceType.BEHAVIORAL_INSTABILITY,
    EvidenceType.BEHAVIORAL_PLATEAU,
    EvidenceType.LEADERSHIP_STRONG,
    EvidenceType.LEADERSHIP_EMERGING,
    EvidenceType.LEADERSHIP_ABSENT,
    EvidenceType.COLLABORATION_STRONG,
    EvidenceType.COLLABORATION_EFFECTIVE,
    EvidenceType.COLLABORATION_DEFICIT,
    EvidenceType.ADAPTABILITY_HIGH,
    EvidenceType.ADAPTABILITY_MODERATE,
    EvidenceType.ADAPTABILITY_LOW,
})

_MIN_BEHAVIORAL_SIGNALS = 2


class BehavioralGrowthObservationRule(ObservationRule):
    """Detects behavioral growth or plateau from behavioral/soft-skill signals."""

    @property
    def rule_id(self) -> str:
        return "behavioral_growth_rule"

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.LOW

    @property
    def description(self) -> str:
        return "Detects behavioral growth or plateau from behavioral, adaptability, leadership, and collaboration signals"

    def applies_to(self, context: ObservationExtractionContext) -> bool:
        behavioral_signals = [s for s in context.signals if s.signal_type in _BEHAVIORAL_SIGNAL_TYPES]
        return len(behavioral_signals) >= _MIN_BEHAVIORAL_SIGNALS

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        behavioral_signals = [s for s in context.signals if s.signal_type in _BEHAVIORAL_SIGNAL_TYPES]

        if len(behavioral_signals) < _MIN_BEHAVIORAL_SIGNALS:
            return []

        positive = [s for s in behavioral_signals if s.polarity == EvidencePolarity.POSITIVE]
        negative = [s for s in behavioral_signals if s.polarity == EvidencePolarity.NEGATIVE]

        if len(positive) >= _MIN_BEHAVIORAL_SIGNALS and len(positive) >= len(negative):
            avg_strength = sum(s.strength for s in positive) / len(positive)
            ratio = len(positive) / len(behavioral_signals)
            confidence = round(min(1.0, avg_strength * 0.65 + ratio * 0.35), 4)
            return [
                ObservationRuleMatch(
                    rule_id=self.rule_id,
                    observation_type=ObservationType.BEHAVIORAL_GROWTH,
                    confidence=confidence,
                    description="Behavioral growth pattern detected",
                    tags=frozenset({"behavioral_growth"}),
                    rationale=(
                        f"total_behavioral={len(behavioral_signals)}, "
                        f"positive={len(positive)}, negative={len(negative)}, "
                        f"avg_positive_strength={avg_strength:.3f}, confidence={confidence}"
                    ),
                )
            ]

        if len(negative) > len(positive):
            avg_strength = sum(s.strength for s in negative) / len(negative)
            inverted = 1.0 - avg_strength
            ratio = len(negative) / len(behavioral_signals)
            confidence = round(min(1.0, inverted * 0.65 + ratio * 0.35), 4)
            return [
                ObservationRuleMatch(
                    rule_id=self.rule_id,
                    observation_type=ObservationType.BEHAVIORAL_PLATEAU,
                    confidence=confidence,
                    description="Behavioral plateau pattern detected",
                    tags=frozenset({"behavioral_plateau"}),
                    rationale=(
                        f"total_behavioral={len(behavioral_signals)}, "
                        f"positive={len(positive)}, negative={len(negative)}, "
                        f"avg_negative_strength={avg_strength:.3f}, confidence={confidence}"
                    ),
                )
            ]

        return []
