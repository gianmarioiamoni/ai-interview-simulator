# tests/domain/contracts/observation/extraction/test_observation_rule_registry.py

import pytest

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.extraction.observation_rule_registry import (
    DuplicateRuleError,
    ObservationRuleRegistry,
)
from tests.domain.contracts.observation.extraction.conftest import AlwaysMatchRule, NeverMatchRule


class TestObservationRuleRegistryConstruction:
    def test_initial_rule_count_zero(self):
        r = ObservationRuleRegistry()
        assert r.rule_count() == 0

    def test_not_frozen_initially(self):
        r = ObservationRuleRegistry()
        assert not r.is_frozen()

    def test_rule_ids_empty_initially(self):
        r = ObservationRuleRegistry()
        assert r.rule_ids() == frozenset()


class TestObservationRuleRegistryRegister:
    def test_register_increments_count(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="r1"))
        assert r.rule_count() == 1

    def test_register_multiple(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="r1"))
        r.register(NeverMatchRule(rule_id="r2"))
        assert r.rule_count() == 2

    def test_register_adds_to_rule_ids(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="my-rule"))
        assert "my-rule" in r.rule_ids()

    def test_get_registered_rule(self):
        r = ObservationRuleRegistry()
        rule = AlwaysMatchRule(rule_id="r1")
        r.register(rule)
        assert r.get("r1") is rule

    def test_get_nonexistent_returns_none(self):
        r = ObservationRuleRegistry()
        assert r.get("nonexistent") is None

    def test_duplicate_rule_id_raises(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="dup"))
        with pytest.raises(DuplicateRuleError):
            r.register(AlwaysMatchRule(rule_id="dup"))

    def test_register_after_freeze_raises(self):
        r = ObservationRuleRegistry()
        r.freeze()
        with pytest.raises(RuntimeError):
            r.register(AlwaysMatchRule(rule_id="late"))

    def test_empty_rule_id_raises(self):
        r = ObservationRuleRegistry()

        class EmptyIdRule(AlwaysMatchRule):
            @property
            def rule_id(self) -> str:
                return ""

        with pytest.raises(ValueError):
            r.register(EmptyIdRule())

    def test_whitespace_rule_id_raises(self):
        r = ObservationRuleRegistry()

        class WhitespaceIdRule(AlwaysMatchRule):
            @property
            def rule_id(self) -> str:
                return "   "

        with pytest.raises(ValueError):
            r.register(WhitespaceIdRule())


class TestObservationRuleRegistryFreeze:
    def test_freeze_sets_frozen(self):
        r = ObservationRuleRegistry()
        r.freeze()
        assert r.is_frozen()

    def test_freeze_twice_is_noop(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="r1"))
        r.freeze()
        r.freeze()  # second freeze should not raise
        assert r.is_frozen()

    def test_ordered_rules_requires_freeze(self):
        r = ObservationRuleRegistry()
        with pytest.raises(RuntimeError):
            r.ordered_rules()

    def test_rules_by_priority_requires_freeze(self):
        r = ObservationRuleRegistry()
        with pytest.raises(RuntimeError):
            r.rules_by_priority(ObservationRulePriority.NORMAL)


class TestObservationRuleRegistryOrdering:
    def test_priority_order_ascending(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="low", priority=ObservationRulePriority.LOW))
        r.register(AlwaysMatchRule(rule_id="critical", priority=ObservationRulePriority.CRITICAL))
        r.register(AlwaysMatchRule(rule_id="normal", priority=ObservationRulePriority.NORMAL))
        r.freeze()
        ids = [rule.rule_id for rule in r.ordered_rules()]
        assert ids == ["critical", "normal", "low"]

    def test_same_priority_tiebreak_by_rule_id(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="zzz", priority=ObservationRulePriority.NORMAL))
        r.register(AlwaysMatchRule(rule_id="aaa", priority=ObservationRulePriority.NORMAL))
        r.register(AlwaysMatchRule(rule_id="mmm", priority=ObservationRulePriority.NORMAL))
        r.freeze()
        ids = [rule.rule_id for rule in r.ordered_rules()]
        assert ids == ["aaa", "mmm", "zzz"]

    def test_mixed_priority_and_id_tiebreak(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="b-normal", priority=ObservationRulePriority.NORMAL))
        r.register(AlwaysMatchRule(rule_id="a-normal", priority=ObservationRulePriority.NORMAL))
        r.register(AlwaysMatchRule(rule_id="a-high", priority=ObservationRulePriority.HIGH))
        r.register(AlwaysMatchRule(rule_id="z-critical", priority=ObservationRulePriority.CRITICAL))
        r.freeze()
        ids = [rule.rule_id for rule in r.ordered_rules()]
        assert ids == ["z-critical", "a-high", "a-normal", "b-normal"]

    def test_ordered_rules_is_tuple(self):
        r = ObservationRuleRegistry()
        r.freeze()
        assert isinstance(r.ordered_rules(), tuple)

    def test_order_stable_after_multiple_calls(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="b"))
        r.register(AlwaysMatchRule(rule_id="a"))
        r.freeze()
        order1 = [rule.rule_id for rule in r.ordered_rules()]
        order2 = [rule.rule_id for rule in r.ordered_rules()]
        assert order1 == order2

    def test_rules_by_priority_returns_correct_subset(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="h1", priority=ObservationRulePriority.HIGH))
        r.register(AlwaysMatchRule(rule_id="n1", priority=ObservationRulePriority.NORMAL))
        r.register(AlwaysMatchRule(rule_id="h2", priority=ObservationRulePriority.HIGH))
        r.freeze()
        high_rules = r.rules_by_priority(ObservationRulePriority.HIGH)
        assert len(high_rules) == 2
        assert all(rule.priority == ObservationRulePriority.HIGH for rule in high_rules)

    def test_rules_by_priority_ordered_by_id(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="zz", priority=ObservationRulePriority.NORMAL))
        r.register(AlwaysMatchRule(rule_id="aa", priority=ObservationRulePriority.NORMAL))
        r.freeze()
        rules = r.rules_by_priority(ObservationRulePriority.NORMAL)
        ids = [rule.rule_id for rule in rules]
        assert ids == sorted(ids)

    def test_rules_by_priority_empty_for_unused_priority(self):
        r = ObservationRuleRegistry()
        r.register(AlwaysMatchRule(rule_id="r1", priority=ObservationRulePriority.NORMAL))
        r.freeze()
        critical_rules = r.rules_by_priority(ObservationRulePriority.CRITICAL)
        assert len(critical_rules) == 0

    def test_empty_registry_ordered_rules_empty(self):
        r = ObservationRuleRegistry()
        r.freeze()
        assert r.ordered_rules() == ()
