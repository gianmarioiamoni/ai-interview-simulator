# domain/contracts/observation/extraction/observation_rule.py
# ADR-016: ObservationRule — abstract plugin contract

from abc import ABC, abstractmethod

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority


class ObservationRule(ABC):
    """Abstract base for all Observation extraction rules.

    Plugin contract (ADR-016 Section F):
    - Each rule is stateless and independent.
    - A rule inspects the extraction context and emits zero or more matches.
    - Rules must be deterministic: same context always yields the same matches.
    - Rules must not mutate the context or any shared state.
    - Rules must not call LLMs or any I/O.
    - rule_id must be unique across the registry.
    - priority controls execution order (lower value = higher priority).

    Lifecycle:
        Rules are registered in ObservationRuleRegistry at startup.
        ObservationExtractor invokes evaluate() on each rule in priority order.
        Matches are collected and converted to Observations by the extractor.
    """

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique, stable identifier for this rule.

        Must be non-empty, contain only ASCII printable chars, and remain
        stable across software versions (used for audit and diagnostics).
        """

    @property
    @abstractmethod
    def priority(self) -> ObservationRulePriority:
        """Execution priority. Lower = higher priority."""

    @property
    def description(self) -> str:
        """Human-readable description of what this rule detects.

        Optional — returns empty string by default.
        """
        return ""

    @abstractmethod
    def evaluate(
        self, context: ObservationExtractionContext
    ) -> list[ObservationRuleMatch]:
        """Evaluate the context and return zero or more rule matches.

        Invariants:
        - Must be deterministic for the same context.
        - Must be side-effect free.
        - Must not raise unless an unrecoverable programming error occurs;
          domain-level non-matches should return an empty list.
        - Returned matches must have rule_id equal to self.rule_id.
        """

    def applies_to(self, context: ObservationExtractionContext) -> bool:
        """Optional fast-path guard — return False to skip evaluate().

        Default implementation always returns True (always evaluated).
        Override for cheap pre-filtering to avoid unnecessary work.
        """
        return True
