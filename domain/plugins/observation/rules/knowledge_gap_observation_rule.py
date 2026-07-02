# domain/plugins/observation/rules/knowledge_gap_observation_rule.py

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

_KNOWLEDGE_DIMENSIONS = frozenset({
    ProfileDimension.TECHNICAL_DEPTH,
    ProfileDimension.ENGINEERING_JUDGMENT,
})

_GAP_SIGNAL_TYPES = frozenset({
    EvidenceType.KNOWLEDGE_GAP,
    EvidenceType.MISSING_EVIDENCE,
    EvidenceType.SHALLOW_ANSWER,
    EvidenceType.REASONING_GAP,
})


class KnowledgeGapObservationRule(ObservationRule):
    """Detects knowledge gaps from negative-polarity signals."""

    @property
    def rule_id(self) -> str:
        return "knowledge_gap_rule"

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.HIGH

    @property
    def description(self) -> str:
        return "Detects knowledge gaps from weak or gap-typed negative signals"

    def applies_to(self, context: ObservationExtractionContext) -> bool:
        return any(s.polarity == EvidencePolarity.NEGATIVE for s in context.signals)

    def evaluate(self, context: ObservationExtractionContext) -> list[ObservationRuleMatch]:
        matches: list[ObservationRuleMatch] = []

        gap_signals = [
            s for s in context.signals
            if s.polarity == EvidencePolarity.NEGATIVE
            and (s.strength <= 0.3 or s.signal_type in _GAP_SIGNAL_TYPES or s.dimension in _KNOWLEDGE_DIMENSIONS)
        ]

        if not gap_signals:
            return matches

        by_dimension: dict[ProfileDimension, list] = {}
        for sig in gap_signals:
            by_dimension.setdefault(sig.dimension, []).append(sig)

        for dimension, sigs in sorted(by_dimension.items(), key=lambda x: x[0].value):
            avg_strength = sum(s.strength for s in sigs) / len(sigs)
            confidence = round(min(1.0, max(0.0, 1.0 - avg_strength)), 4)
            matches.append(
                ObservationRuleMatch(
                    rule_id=self.rule_id,
                    observation_type=ObservationType.KNOWLEDGE_GAP,
                    confidence=confidence,
                    description=f"Knowledge gap detected in {dimension.value}",
                    tags=frozenset({"knowledge_gap", dimension.value}),
                    rationale=(
                        f"dimension={dimension.value}, signal_count={len(sigs)}, "
                        f"avg_strength={avg_strength:.3f}, confidence={confidence}"
                    ),
                )
            )

        return matches
