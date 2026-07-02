# tests/domain/contracts/observation/extraction/test_observation_rule.py

import inspect

import pytest

from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from tests.domain.contracts.observation.extraction.conftest import (
    AlwaysMatchRule,
    NeverMatchRule,
    SkipRule,
    ErrorRule,
    make_context,
)


class TestObservationRuleIsAbstract:
    def test_is_abstract(self):
        assert inspect.isabstract(ObservationRule)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            ObservationRule()  # type: ignore[abstract]

    def test_abstract_methods_declared(self):
        expected = {"rule_id", "priority", "evaluate"}
        assert expected.issubset(ObservationRule.__abstractmethods__)


class TestObservationRuleDefaults:
    def test_applies_to_returns_true_by_default(self):
        rule = AlwaysMatchRule()
        ctx = make_context()
        assert rule.applies_to(ctx) is True

    def test_description_returns_empty_by_default(self):
        rule = AlwaysMatchRule()
        assert rule.description == ""


class TestAlwaysMatchRule:
    def test_rule_id_set(self):
        rule = AlwaysMatchRule(rule_id="test-rule")
        assert rule.rule_id == "test-rule"

    def test_priority_set(self):
        rule = AlwaysMatchRule(priority=ObservationRulePriority.HIGH)
        assert rule.priority == ObservationRulePriority.HIGH

    def test_evaluate_returns_one_match(self):
        rule = AlwaysMatchRule()
        matches = rule.evaluate(make_context())
        assert len(matches) == 1

    def test_evaluate_returns_rule_match_type(self):
        rule = AlwaysMatchRule()
        matches = rule.evaluate(make_context())
        assert isinstance(matches[0], ObservationRuleMatch)

    def test_evaluate_match_has_correct_rule_id(self):
        rule = AlwaysMatchRule(rule_id="my-rule")
        matches = rule.evaluate(make_context())
        assert matches[0].rule_id == "my-rule"

    def test_evaluate_deterministic(self):
        rule = AlwaysMatchRule()
        ctx = make_context()
        result1 = rule.evaluate(ctx)
        result2 = rule.evaluate(ctx)
        assert result1[0].observation_type == result2[0].observation_type
        assert result1[0].confidence == result2[0].confidence


class TestNeverMatchRule:
    def test_evaluate_returns_empty(self):
        rule = NeverMatchRule()
        assert rule.evaluate(make_context()) == []

    def test_applies_to_true(self):
        rule = NeverMatchRule()
        assert rule.applies_to(make_context()) is True


class TestSkipRule:
    def test_applies_to_returns_false(self):
        rule = SkipRule()
        assert rule.applies_to(make_context()) is False


class TestErrorRule:
    def test_evaluate_raises(self):
        rule = ErrorRule()
        with pytest.raises(RuntimeError):
            rule.evaluate(make_context())


class TestObservationRulePriorityVariants:
    def test_critical_priority_rule(self):
        rule = AlwaysMatchRule(priority=ObservationRulePriority.CRITICAL)
        assert rule.priority == ObservationRulePriority.CRITICAL

    def test_fallback_priority_rule(self):
        rule = AlwaysMatchRule(priority=ObservationRulePriority.FALLBACK)
        assert rule.priority == ObservationRulePriority.FALLBACK

    def test_all_priorities_valid(self):
        for p in ObservationRulePriority:
            rule = AlwaysMatchRule(priority=p)
            assert rule.priority == p
