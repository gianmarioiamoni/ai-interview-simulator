# domain/plugins/observation/rules/repeated_weakness_observation_rule.py

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.profile_dimension import ProfileDimension

_MIN_SIGNAL_COUNT = 2


class RepeatedWeaknessObservationRule(ObservationRule):
    """Detects repeated negative signals on the same dimension."""

    @property
    def rule_id(self) -> str:
        return "repeated_weakness_rule"

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.NORMAL

    @property
    def description(self) -> str:
        return "Detects repeated negative signals indicating shallow technical knowledge on a dimension"

    def applies_to(self, context: ObservationExtractionContext) -> bool:
        return any(s.polarity == EvidencePolarity.NEGATIVE for s in context.signals)

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        negative_signals = [s for s in context.signals if s.polarity == EvidencePolarity.NEGATIVE]

        by_dimension: dict[ProfileDimension, list] = {}
        for sig in negative_signals:
            by_dimension.setdefault(sig.dimension, []).append(sig)

        matches: list[ObservationRuleMatch] = []
        for dimension, sigs in sorted(by_dimension.items(), key=lambda x: x[0].value):
            if len(sigs) < _MIN_SIGNAL_COUNT:
                continue
            avg_strength = sum(s.strength for s in sigs) / len(sigs)
            count_factor = min(1.0, len(sigs) / 5.0)
            inverted_strength = 1.0 - avg_strength
            confidence = round(min(1.0, inverted_strength * 0.7 + count_factor * 0.3), 4)
            matches.append(
                ObservationRuleMatch(
                    rule_id=self.rule_id,
                    observation_type=ObservationType.TECHNICAL_SHALLOW,
                    confidence=confidence,
                    description=f"Repeated weakness detected in {dimension.value}",
                    tags=frozenset({"repeated_weakness", dimension.value}),
                    rationale=(
                        f"dimension={dimension.value}, count={len(sigs)}, "
                        f"avg_strength={avg_strength:.3f}, confidence={confidence}"
                    ),
                )
            )

        return matches
