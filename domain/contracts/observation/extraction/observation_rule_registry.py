# domain/contracts/observation/extraction/observation_rule_registry.py
# ADR-016: Rule registry — frozen, ordered, plugin-based

from __future__ import annotations

from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority


class DuplicateRuleError(ValueError):
    """Raised when a rule with a duplicate rule_id is registered."""


class ObservationRuleRegistry:
    """Ordered, frozen registry of ObservationRule plugins.

    Rules are registered before the registry is frozen. After freeze(),
    no further registrations are accepted. This ensures the rule set is
    stable and deterministic across the entire extraction session (ADR-016).

    Ordering invariants:
    - Rules are stored in execution order: ascending priority value,
      tie-broken by rule_id lexicographic order.
    - Order is fixed at freeze() time and never changes thereafter.
    - Duplicate rule_id raises DuplicateRuleError immediately on register().

    Usage:
        registry = ObservationRuleRegistry()
        registry.register(MyRule())
        registry.freeze()
        rules = registry.ordered_rules()  # stable, deterministic
    """

    def __init__(self) -> None:
        self._rules: dict[str, ObservationRule] = {}
        self._frozen: bool = False
        self._ordered: tuple[ObservationRule, ...] = ()

    def register(self, rule: ObservationRule) -> None:
        """Register a rule. Raises if frozen or rule_id already registered.

        Raises:
            RuntimeError: if the registry is already frozen.
            DuplicateRuleError: if a rule with the same rule_id is already registered.
            ValueError: if rule_id is empty.
        """
        if self._frozen:
            raise RuntimeError(
                "ObservationRuleRegistry is frozen; no further registrations accepted."
            )
        rule_id = rule.rule_id
        if not rule_id or not rule_id.strip():
            raise ValueError("rule_id must be non-empty")
        if rule_id in self._rules:
            raise DuplicateRuleError(
                f"Rule with rule_id={rule_id!r} is already registered."
            )
        self._rules[rule_id] = rule

    def freeze(self) -> None:
        """Freeze the registry. Computes and locks the execution order.

        After freeze(), ordered_rules() returns a stable tuple.
        Calling freeze() more than once is a no-op.
        """
        if self._frozen:
            return
        self._ordered = tuple(
            sorted(
                self._rules.values(),
                key=lambda r: (r.priority.value, r.rule_id),
            )
        )
        self._frozen = True

    def ordered_rules(self) -> tuple[ObservationRule, ...]:
        """Return the rules in execution order (priority ASC, rule_id ASC).

        Raises:
            RuntimeError: if the registry has not been frozen yet.
        """
        if not self._frozen:
            raise RuntimeError(
                "Registry must be frozen before ordered_rules() is called."
            )
        return self._ordered

    def get(self, rule_id: str) -> ObservationRule | None:
        """Return the rule with the given rule_id, or None."""
        return self._rules.get(rule_id)

    def is_frozen(self) -> bool:
        """Return True if the registry has been frozen."""
        return self._frozen

    def rule_count(self) -> int:
        """Return the number of registered rules."""
        return len(self._rules)

    def rule_ids(self) -> frozenset[str]:
        """Return the set of registered rule IDs."""
        return frozenset(self._rules.keys())

    def rules_by_priority(
        self, priority: ObservationRulePriority
    ) -> tuple[ObservationRule, ...]:
        """Return all rules with the given priority in rule_id order.

        Requires the registry to be frozen.
        """
        if not self._frozen:
            raise RuntimeError("Registry must be frozen before querying by priority.")
        return tuple(r for r in self._ordered if r.priority == priority)
