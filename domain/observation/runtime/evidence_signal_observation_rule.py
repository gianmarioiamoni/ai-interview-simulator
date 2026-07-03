# domain/observation/runtime/evidence_signal_observation_rule.py
# ADR-016: EvidenceSignalObservationRule — maps EvidenceSignal → ObservationRuleMatch
#
# This rule is the canonical bridge between the V1.1 EvidenceStore and the
# V1.2 ObservationStore.  It runs once per extraction cycle and converts
# all signals in the context into typed ObservationRuleMatches.
#
# Invariants:
# - Stateless: no mutable state between invocations.
# - Deterministic: same signals always yield the same matches.
# - No LLM, no I/O.
# - Signals with no mapping entry are skipped (never raise).

from __future__ import annotations

from domain.contracts.observation.extraction.observation_extraction_context import (
    ObservationExtractionContext,
)
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_type import EvidenceType

# ---------------------------------------------------------------------------
# EvidenceType → ObservationType mapping (ADR-016, ADR-066)
# Only bijective, semantically equivalent mappings are listed.
# Unmapped EvidenceTypes are silently skipped.
# ---------------------------------------------------------------------------
_EVIDENCE_TYPE_TO_OBSERVATION_TYPE: dict[EvidenceType, ObservationType] = {
    # Technical
    EvidenceType.KNOWLEDGE_GAP: ObservationType.KNOWLEDGE_GAP,
    EvidenceType.SHALLOW_ANSWER: ObservationType.TECHNICAL_SHALLOW,
    EvidenceType.REPEATED_STRENGTH: ObservationType.TECHNICAL_STRENGTH,
    EvidenceType.RECOVERED_WEAKNESS: ObservationType.TECHNICAL_RECOVERED,

    # Reasoning
    EvidenceType.REASONING_GAP: ObservationType.TECHNICAL_GAP,
    EvidenceType.REASONING_DEPTH_HIGH: ObservationType.REASONING_DEPTH_HIGH,
    EvidenceType.REASONING_DEPTH_LOW: ObservationType.REASONING_DEPTH_LOW,
    EvidenceType.REASONING_IMPROVING: ObservationType.REASONING_IMPROVING,
    EvidenceType.REASONING_STAGNATING: ObservationType.REASONING_STAGNATING,
    EvidenceType.CONTRADICTORY_ANSWER: ObservationType.REASONING_CONTRADICTORY,

    # Engineering judgment
    EvidenceType.ENGINEERING_JUDGMENT_HIGH: ObservationType.ENGINEERING_JUDGMENT_HIGH,
    EvidenceType.ENGINEERING_JUDGMENT_LOW: ObservationType.ENGINEERING_JUDGMENT_LOW,
    EvidenceType.ENGINEERING_JUDGMENT_ARTICULATED: ObservationType.ENGINEERING_JUDGMENT_ARTICULATED,

    # Communication
    EvidenceType.COMMUNICATION_GAP: ObservationType.COMMUNICATION_GAP,
    EvidenceType.COMMUNICATION_CLEAR: ObservationType.COMMUNICATION_CLEAR,
    EvidenceType.COMMUNICATION_WEAK: ObservationType.COMMUNICATION_WEAK,
    EvidenceType.COMMUNICATION_INCONSISTENT: ObservationType.COMMUNICATION_INCONSISTENT,

    # Confidence
    EvidenceType.CONFIDENCE_DROP: ObservationType.CONFIDENCE_DROP,
    EvidenceType.DEMONSTRATED_DEPTH: ObservationType.TECHNICAL_DEPTH,

    # Behavioral
    EvidenceType.BEHAVIORAL_GROWTH: ObservationType.BEHAVIORAL_GROWTH,
    EvidenceType.BEHAVIORAL_INSTABILITY: ObservationType.BEHAVIORAL_INSTABILITY,
}

# Confidence value to assign to all converted matches.
# Signals are binary (they exist or they don't); 0.85 is the canonical
# non-trivial confidence for rule-based matches (consistent with test stubs).
_RULE_CONFIDENCE = 0.85


class EvidenceSignalObservationRule(ObservationRule):
    """Converts EvidenceSignals in the extraction context into ObservationRuleMatches.

    This is the sole rule in the default registry for V1.2 Phase C integration.
    One match is emitted per signal with a known ObservationType mapping.
    Unmapped signal types are silently skipped.
    """

    RULE_ID = "evidence_signal_to_observation"

    @property
    def rule_id(self) -> str:
        return self.RULE_ID

    @property
    def priority(self) -> ObservationRulePriority:
        return ObservationRulePriority.HIGH

    @property
    def description(self) -> str:
        return "Maps EvidenceSignal[] to ObservationRuleMatch[] via EvidenceType→ObservationType table."

    def evaluate(
        self, context: ObservationExtractionContext
    ) -> list[ObservationRuleMatch]:
        matches: list[ObservationRuleMatch] = []
        for signal in context.signals:
            obs_type = _EVIDENCE_TYPE_TO_OBSERVATION_TYPE.get(signal.signal_type)
            if obs_type is None:
                continue
            matches.append(
                ObservationRuleMatch(
                    rule_id=self.RULE_ID,
                    observation_type=obs_type,
                    confidence=_RULE_CONFIDENCE,
                    description=f"{signal.signal_type.value} signal at q{context.question_index}",
                    tags=frozenset({signal.signal_type.value, signal.source.value}),
                    rationale=f"polarity={signal.polarity.value} source={signal.source.value}",
                )
            )
        return matches
