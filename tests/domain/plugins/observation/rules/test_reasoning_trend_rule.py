# tests/domain/plugins/observation/rules/test_reasoning_trend_rule.py

import pytest

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.plugins.observation.rules.reasoning_trend_observation_rule import ReasoningTrendObservationRule
from tests.domain.plugins.observation.rules.conftest import make_context, make_signal


@pytest.fixture
def rule():
    return ReasoningTrendObservationRule()


def make_reasoning_signal(polarity: EvidencePolarity, strength: float = 0.7, signal_type: EvidenceType = EvidenceType.REASONING_DEPTH_HIGH):
    return make_signal(
        dimension=ProfileDimension.PROBLEM_SOLVING,
        polarity=polarity,
        signal_type=signal_type,
        strength=strength,
    )


# --- Interface ---

class TestReasoningTrendInterface:
    def test_rule_id(self, rule):
        assert rule.rule_id == "reasoning_trend_rule"

    def test_priority(self, rule):
        assert rule.priority == ObservationRulePriority.HIGH

    def test_priority_value(self, rule):
        assert rule.priority.value == 20

    def test_description_non_empty(self, rule):
        assert len(rule.description) > 0

    def test_is_observation_rule(self, rule):
        from domain.contracts.observation.extraction.observation_rule import ObservationRule
        assert isinstance(rule, ObservationRule)


# --- applies_to ---

class TestReasoningTrendAppliesTo:
    def test_applies_with_two_reasoning_signals(self, rule):
        sig1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        sig2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is True

    def test_does_not_apply_with_one_reasoning_signal(self, rule):
        sig = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig])
        assert rule.applies_to(ctx) is False

    def test_applies_with_reasoning_signal_type_not_problem_solving_dim(self, rule):
        sig1 = make_signal(
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.POSITIVE,
            signal_type=EvidenceType.REASONING_IMPROVING,
        )
        sig2 = make_signal(
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.REASONING_STAGNATING,
        )
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is True

    def test_does_not_apply_non_reasoning_signals(self, rule):
        sig1 = make_signal(dimension=ProfileDimension.COMMUNICATION, polarity=EvidencePolarity.POSITIVE)
        sig2 = make_signal(dimension=ProfileDimension.COMMUNICATION, polarity=EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        assert rule.applies_to(ctx) is False


# --- evaluate: no match ---

class TestReasoningTrendNoMatch:
    def test_single_reasoning_signal_no_match(self, rule):
        sig = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig])
        assert rule.evaluate(ctx) == []

    def test_equal_positive_negative_no_match(self, rule):
        pos = make_reasoning_signal(EvidencePolarity.POSITIVE)
        neg = make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_DEPTH_LOW)
        ctx = make_context([pos, neg])
        assert rule.evaluate(ctx) == []

    def test_returns_list_type(self, rule):
        sig = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([sig])
        result = rule.evaluate(ctx)
        assert isinstance(result, list)

    def test_non_reasoning_signals_no_match(self, rule):
        sig1 = make_signal(dimension=ProfileDimension.COMMUNICATION, polarity=EvidencePolarity.POSITIVE)
        sig2 = make_signal(dimension=ProfileDimension.COMMUNICATION, polarity=EvidencePolarity.POSITIVE)
        ctx = make_context([sig1, sig2])
        assert rule.evaluate(ctx) == []


# --- evaluate: improving trend ---

class TestReasoningTrendImproving:
    def test_majority_positive_yields_improving(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        neg = make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_DEPTH_LOW)
        ctx = make_context([pos1, pos2, neg])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.REASONING_IMPROVING

    def test_all_positive_yields_improving(self, rule):
        sigs = [make_reasoning_signal(EvidencePolarity.POSITIVE) for _ in range(3)]
        ctx = make_context(sigs)
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.REASONING_IMPROVING

    def test_improving_via_signal_type(self, rule):
        sig1 = make_signal(
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.POSITIVE,
            signal_type=EvidenceType.REASONING_IMPROVING,
        )
        sig2 = make_signal(
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.POSITIVE,
            signal_type=EvidenceType.REASONING_IMPROVING,
        )
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.REASONING_IMPROVING


# --- evaluate: stagnating trend ---

class TestReasoningTrendStagnating:
    def test_majority_negative_yields_stagnating(self, rule):
        neg1 = make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_DEPTH_LOW)
        neg2 = make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_DEPTH_LOW)
        pos = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([neg1, neg2, pos])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.REASONING_STAGNATING

    def test_all_negative_yields_stagnating(self, rule):
        sigs = [make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_STAGNATING) for _ in range(3)]
        ctx = make_context(sigs)
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.REASONING_STAGNATING

    def test_stagnating_via_signal_type(self, rule):
        sig1 = make_signal(
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.REASONING_STAGNATING,
        )
        sig2 = make_signal(
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.REASONING_GAP,
        )
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.REASONING_STAGNATING


# --- Match content ---

class TestReasoningTrendMatchContent:
    def test_rule_id_in_match(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([pos1, pos2])
        match = rule.evaluate(ctx)[0]
        assert match.rule_id == "reasoning_trend_rule"

    def test_confidence_in_range(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE, strength=0.8)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE, strength=0.7)
        ctx = make_context([pos1, pos2])
        match = rule.evaluate(ctx)[0]
        assert 0.0 <= match.confidence <= 1.0

    def test_description_non_empty(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([pos1, pos2])
        match = rule.evaluate(ctx)[0]
        assert len(match.description) > 0

    def test_tags_include_reasoning_trend(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([pos1, pos2])
        match = rule.evaluate(ctx)[0]
        assert "reasoning_trend" in match.tags

    def test_tags_include_trend_label_improving(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([pos1, pos2])
        match = rule.evaluate(ctx)[0]
        assert "improving" in match.tags

    def test_tags_include_trend_label_stagnating(self, rule):
        neg1 = make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_STAGNATING)
        neg2 = make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_STAGNATING)
        ctx = make_context([neg1, neg2])
        match = rule.evaluate(ctx)[0]
        assert "stagnating" in match.tags

    def test_rationale_non_empty(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([pos1, pos2])
        match = rule.evaluate(ctx)[0]
        assert len(match.rationale) > 0


# --- Determinism ---

class TestReasoningTrendDeterminism:
    def test_same_context_same_output(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        ctx = make_context([pos1, pos2])
        assert rule.evaluate(ctx) == rule.evaluate(ctx)

    def test_multiple_calls_identical(self, rule):
        sigs = [make_reasoning_signal(EvidencePolarity.POSITIVE) for _ in range(3)]
        ctx = make_context(sigs)
        results = [rule.evaluate(ctx) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_single_match_produced(self, rule):
        pos1 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        pos2 = make_reasoning_signal(EvidencePolarity.POSITIVE)
        neg = make_reasoning_signal(EvidencePolarity.NEGATIVE, signal_type=EvidenceType.REASONING_DEPTH_LOW)
        ctx = make_context([pos1, pos2, neg])
        assert len(rule.evaluate(ctx)) == 1
