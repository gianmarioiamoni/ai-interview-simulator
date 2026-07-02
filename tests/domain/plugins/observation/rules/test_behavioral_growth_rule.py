# tests/domain/plugins/observation/rules/test_behavioral_growth_rule.py

import pytest

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.plugins.observation.rules.behavioral_growth_observation_rule import BehavioralGrowthObservationRule
from tests.domain.plugins.observation.rules.conftest import make_context, make_signal


@pytest.fixture
def rule():
    return BehavioralGrowthObservationRule()


def make_behavioral_signal(
    polarity: EvidencePolarity,
    signal_type: EvidenceType = EvidenceType.BEHAVIORAL_GROWTH,
    strength: float = 0.7,
    dimension: ProfileDimension = ProfileDimension.COMMUNICATION,
):
    return make_signal(
        dimension=dimension,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
    )


# --- Interface ---

class TestBehavioralGrowthInterface:
    def test_rule_id(self, rule):
        assert rule.rule_id == "behavioral_growth_rule"

    def test_priority(self, rule):
        assert rule.priority == ObservationRulePriority.LOW

    def test_priority_value(self, rule):
        assert rule.priority.value == 80

    def test_description_non_empty(self, rule):
        assert len(rule.description) > 0

    def test_is_observation_rule(self, rule):
        from domain.contracts.observation.extraction.observation_rule import ObservationRule
        assert isinstance(rule, ObservationRule)


# --- applies_to ---

class TestBehavioralGrowthAppliesTo:
    def test_applies_with_two_behavioral_signals(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is True

    def test_does_not_apply_with_one_behavioral_signal(self, rule):
        sig = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig])
        assert rule.applies_to(ctx) is False

    def test_applies_with_leadership_signals(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.LEADERSHIP_STRONG)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.LEADERSHIP_EMERGING)
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is True

    def test_applies_with_adaptability_signals(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.ADAPTABILITY_HIGH)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.ADAPTABILITY_MODERATE)
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is True

    def test_applies_with_collaboration_signals(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.COLLABORATION_STRONG)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.COLLABORATION_EFFECTIVE)
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is True

    def test_does_not_apply_with_non_behavioral_signals(self, rule):
        sig1 = make_signal(dimension=ProfileDimension.TECHNICAL_DEPTH, polarity=EvidencePolarity.POSITIVE, signal_type=EvidenceType.DEMONSTRATED_DEPTH)
        sig2 = make_signal(dimension=ProfileDimension.TECHNICAL_DEPTH, polarity=EvidencePolarity.POSITIVE, signal_type=EvidenceType.REPEATED_STRENGTH)
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is False


# --- evaluate: no match ---

class TestBehavioralGrowthNoMatch:
    def test_single_behavioral_signal_no_match(self, rule):
        sig = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig])
        assert rule.evaluate(ctx) == []

    def test_returns_list_type(self, rule):
        sig = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig])
        assert isinstance(rule.evaluate(ctx), list)

    def test_equal_positive_negative_positive_dominated_no_plateau(self, rule):
        pos1 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.BEHAVIORAL_GROWTH)
        pos2 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.BEHAVIORAL_GROWTH)
        neg = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        ctx = make_context([pos1, pos2, neg])
        matches = rule.evaluate(ctx)
        assert any(m.observation_type == ObservationType.BEHAVIORAL_GROWTH for m in matches)

    def test_non_behavioral_signals_no_match(self, rule):
        sig1 = make_signal(dimension=ProfileDimension.TECHNICAL_DEPTH, polarity=EvidencePolarity.POSITIVE)
        sig2 = make_signal(dimension=ProfileDimension.TECHNICAL_DEPTH, polarity=EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        assert rule.evaluate(ctx) == []


# --- evaluate: growth ---

class TestBehavioralGrowthMatches:
    def test_two_positive_behavioral_yields_growth(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_GROWTH

    def test_leadership_signals_yield_growth(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.LEADERSHIP_STRONG)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.LEADERSHIP_EMERGING)
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_GROWTH

    def test_adaptability_signals_yield_growth(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.ADAPTABILITY_HIGH)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.ADAPTABILITY_MODERATE)
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_GROWTH

    def test_collaboration_signals_yield_growth(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.COLLABORATION_STRONG)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE, signal_type=EvidenceType.COLLABORATION_EFFECTIVE)
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_GROWTH

    def test_mixed_positive_dominating_yields_growth(self, rule):
        pos1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        pos2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        pos3 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        neg = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        ctx = make_context([pos1, pos2, pos3, neg])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_GROWTH


# --- evaluate: plateau ---

class TestBehavioralPlateauMatches:
    def test_majority_negative_yields_plateau(self, rule):
        neg1 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        neg2 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        pos = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([neg1, neg2, pos])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_PLATEAU

    def test_all_negative_yields_plateau(self, rule):
        sigs = [make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU) for _ in range(3)]
        ctx = make_context(sigs)
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_PLATEAU

    def test_absence_signals_yield_plateau(self, rule):
        neg1 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.LEADERSHIP_ABSENT)
        neg2 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.COLLABORATION_DEFICIT)
        ctx = make_context([neg1, neg2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_PLATEAU

    def test_low_adaptability_yields_plateau(self, rule):
        neg1 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.ADAPTABILITY_LOW)
        neg2 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_INSTABILITY)
        ctx = make_context([neg1, neg2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.BEHAVIORAL_PLATEAU


# --- Match content ---

class TestBehavioralGrowthMatchContent:
    def test_rule_id_in_growth_match(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert match.rule_id == "behavioral_growth_rule"

    def test_confidence_in_range_growth(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE, strength=0.8)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE, strength=0.7)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert 0.0 <= match.confidence <= 1.0

    def test_description_non_empty_growth(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert len(match.description) > 0

    def test_tags_include_behavioral_growth(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert "behavioral_growth" in match.tags

    def test_tags_include_behavioral_plateau(self, rule):
        neg1 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        neg2 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        ctx = make_context([neg1, neg2])
        match = rule.evaluate(ctx)[0]
        assert "behavioral_plateau" in match.tags

    def test_rationale_non_empty(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        match = rule.evaluate(ctx)[0]
        assert len(match.rationale) > 0

    def test_rule_id_in_plateau_match(self, rule):
        neg1 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        neg2 = make_behavioral_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.BEHAVIORAL_PLATEAU)
        ctx = make_context([neg1, neg2])
        match = rule.evaluate(ctx)[0]
        assert match.rule_id == "behavioral_growth_rule"


# --- Determinism ---

class TestBehavioralGrowthDeterminism:
    def test_same_context_same_output(self, rule):
        sig1 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        sig2 = make_behavioral_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        assert rule.evaluate(ctx) == rule.evaluate(ctx)

    def test_multiple_calls_identical(self, rule):
        sigs = [make_behavioral_signal(EvidencePolarity.POSITIVE) for _ in range(3)]
        ctx = make_context(sigs)
        results = [rule.evaluate(ctx) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_confidence_capped_at_one(self, rule):
        sigs = [make_behavioral_signal(EvidencePolarity.POSITIVE, strength=1.0) for _ in range(10)]
        ctx = make_context(sigs)
        match = rule.evaluate(ctx)[0]
        assert match.confidence <= 1.0
