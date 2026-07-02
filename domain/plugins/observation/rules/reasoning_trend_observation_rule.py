# domain/plugins/observation/rules/reasoning_trend_observation_rule.py

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

_REASONING_SIGNAL_TYPES = frozenset({
    EvidenceType.REASONING_DEPTH_HIGH,
    EvidenceType.REASONING_DEPTH_LOW,
    EvidenceType.REASONING_IMPROVING,
    EvidenceType.REASONING_STAGNATING,
    EvidenceType.REASONING_GAP,
})

_MIN_REASONING_SIGNALS = 2


class ReasoningTrendObservationRule(ObservationRule):
    """Detects reasoning trend from reasoning-dimension signals."""

    @property
    def rule_id(self) -> str:
        return "reasoning_trend_rule"

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.HIGH

    @property
    def description(self) -> str:
        return "Detects improving or stagnating reasoning trend from reasoning-dimension signals"

    def applies_to(self, context: ObservationExtractionContext) -> bool:
        reasoning_signals = [
            s for s in context.signals
            if s.dimension == ProfileDimension.PROBLEM_SOLVING
            or s.signal_type in _REASONING_SIGNAL_TYPES
        ]
        return len(reasoning_signals) >= _MIN_REASONING_SIGNALS

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        reasoning_signals = [
            s for s in context.signals
            if s.dimension == ProfileDimension.PROBLEM_SOLVING
            or s.signal_type in _REASONING_SIGNAL_TYPES
        ]

        if len(reasoning_signals) < _MIN_REASONING_SIGNALS:
            return []

        positive = [s for s in reasoning_signals if s.polarity == EvidencePolarity.POSITIVE]
        negative = [s for s in reasoning_signals if s.polarity == EvidencePolarity.NEGATIVE]

        if len(positive) == len(negative):
            return []

        if len(positive) > len(negative):
            obs_type = ObservationType.REASONING_IMPROVING
            dominant = positive
            label = "improving"
        else:
            obs_type = ObservationType.REASONING_STAGNATING
            dominant = negative
            label = "stagnating"

        avg_strength = sum(s.strength for s in dominant) / len(dominant)
        ratio = len(dominant) / len(reasoning_signals)
        confidence = round(min(1.0, avg_strength * 0.6 + ratio * 0.4), 4)

        return [
            ObservationRuleMatch(
                rule_id=self.rule_id,
                observation_type=obs_type,
                confidence=confidence,
                description=f"Reasoning trend is {label}",
                tags=frozenset({"reasoning_trend", label}),
                rationale=(
                    f"total_reasoning_signals={len(reasoning_signals)}, "
                    f"positive={len(positive)}, negative={len(negative)}, "
                    f"avg_dominant_strength={avg_strength:.3f}, confidence={confidence}"
                ),
            )
        ]
