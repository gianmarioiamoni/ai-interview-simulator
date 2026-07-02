# tests/domain/plugins/observation/rules/test_repeated_weakness_rule.py

import pytest

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.plugins.observation.rules.repeated_weakness_observation_rule import RepeatedWeaknessObservationRule
from tests.domain.plugins.observation.rules.conftest import make_context, make_signal


@pytest.fixture
def rule():
    return RepeatedWeaknessObservationRule()


# --- Interface ---

class TestRepeatedWeaknessInterface:
    def test_rule_id(self, rule):
        assert rule.rule_id == "repeated_weakness_rule"

    def test_priority(self, rule):
        assert rule.priority == ObservationRulePriority.NORMAL

    def test_priority_value(self, rule):
        assert rule.priority.value == 50

    def test_description_non_empty(self, rule):
        assert len(rule.description) > 0

    def test_is_observation_rule(self, rule):
        from domain.contracts.observation.extraction.observation_rule import ObservationRule
        assert isinstance(rule, ObservationRule)


# --- applies_to ---

class TestRepeatedWeaknessAppliesTo:
    def test_applies_when_negative_signal(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([sig])
        assert rule.applies_to(ctx) is True

    def test_does_not_apply_when_only_positive(self, rule):
        sig = make_signal(polarity=EvidencePolarity.POSITIVE)
        ctx = make_context([sig])
        assert rule.applies_to(ctx) is False

    def test_applies_when_mixed(self, rule):
        pos = make_signal(polarity=EvidencePolarity.POSITIVE)
        neg = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([pos, neg])
        assert rule.applies_to(ctx) is True


# --- evaluate: no match cases ---

class TestRepeatedWeaknessNoMatch:
    def test_single_negative_no_match(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.5)
        ctx = make_context([sig])
        assert rule.evaluate(ctx) == []

    def test_only_positive_signals_no_match(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.POSITIVE)
        sig2 = make_signal(polarity=EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        assert rule.evaluate(ctx) == []

    def test_returns_empty_list_type(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([sig])
        result = rule.evaluate(ctx)
        assert isinstance(result, list)

    def test_one_negative_per_different_dimension_no_match(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.PROBLEM_SOLVING)
        ctx = make_context([sig1, sig2])
        assert rule.evaluate(ctx) == []


# --- evaluate: match cases ---

class TestRepeatedWeaknessMatches:
    def test_two_negative_same_dimension_produces_match(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.5)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.4)
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.TECHNICAL_SHALLOW

    def test_three_negative_same_dimension_produces_match(self, rule):
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH)
            for _ in range(3)
        ]
        ctx = make_context(sigs)
        matches = rule.evaluate(ctx)
        assert len(matches) == 1

    def test_two_dimensions_with_repeats_produces_two_matches(self, rule):
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH),
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH),
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.PROBLEM_SOLVING),
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.PROBLEM_SOLVING),
        ]
        ctx = make_context(sigs)
        matches = rule.evaluate(ctx)
        assert len(matches) == 2

    def test_mixed_polarity_only_negative_counted(self, rule):
        neg1 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH)
        neg2 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH)
        pos = make_signal(polarity=EvidencePolarity.POSITIVE, dimension=ProfileDimension.TECHNICAL_DEPTH)
        ctx = make_context([neg1, neg2, pos])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1


# --- Match content ---

class TestRepeatedWeaknessMatchContent:
    def test_rule_id_in_match(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert match.rule_id == "repeated_weakness_rule"

    def test_confidence_in_range(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.5)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.4)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert 0.0 <= match.confidence <= 1.0

    def test_description_non_empty(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert len(match.description) > 0

    def test_tags_include_repeated_weakness(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert "repeated_weakness" in match.tags

    def test_tags_include_dimension(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert "technical_depth" in match.tags

    def test_rationale_non_empty(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert len(match.rationale) > 0

    def test_confidence_higher_for_lower_strength(self, rule):
        low_sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.1) for _ in range(2)]
        high_sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.8) for _ in range(2)]
        ctx_low = make_context(low_sigs)
        ctx_high = make_context(high_sigs)
        assert rule.evaluate(ctx_low)[0].confidence > rule.evaluate(ctx_high)[0].confidence

    def test_confidence_higher_for_more_signals(self, rule):
        two_sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.5) for _ in range(2)]
        five_sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.5) for _ in range(5)]
        ctx2 = make_context(two_sigs)
        ctx5 = make_context(five_sigs)
        assert rule.evaluate(ctx5)[0].confidence >= rule.evaluate(ctx2)[0].confidence


# --- Determinism ---

class TestRepeatedWeaknessDeterminism:
    def test_same_context_same_output(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE)
        ctx = make_context([sig1, sig2])
        assert rule.evaluate(ctx) == rule.evaluate(ctx)

    def test_multiple_calls_identical(self, rule):
        sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE) for _ in range(3)]
        ctx = make_context(sigs)
        results = [rule.evaluate(ctx) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_confidence_capped_at_one(self, rule):
        sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.0) for _ in range(10)]
        ctx = make_context(sigs)
        match = rule.evaluate(ctx)[0]
        assert match.confidence <= 1.0

    def test_confidence_floor_at_zero(self, rule):
        sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE, strength=1.0) for _ in range(2)]
        ctx = make_context(sigs)
        match = rule.evaluate(ctx)[0]
        assert match.confidence >= 0.0

    def test_observation_type_is_technical_shallow(self, rule):
        sigs = [make_signal(polarity=EvidencePolarity.NEGATIVE) for _ in range(2)]
        ctx = make_context(sigs)
        match = rule.evaluate(ctx)[0]
        assert match.observation_type == ObservationType.TECHNICAL_SHALLOW
