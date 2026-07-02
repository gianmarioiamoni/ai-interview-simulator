# tests/domain/plugins/observation/rules/test_knowledge_gap_rule.py

import pytest

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.plugins.observation.rules.knowledge_gap_observation_rule import KnowledgeGapObservationRule
from tests.domain.plugins.observation.rules.conftest import make_context, make_signal


@pytest.fixture
def rule():
    return KnowledgeGapObservationRule()


# --- Interface ---

class TestKnowledgeGapRuleInterface:
    def test_rule_id(self, rule):
        assert rule.rule_id == "knowledge_gap_rule"

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

class TestKnowledgeGapAppliesTo:
    def test_applies_when_negative_signal_present(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        assert rule.applies_to(ctx) is True

    def test_does_not_apply_when_only_positive_signals(self, rule):
        sig = make_signal(polarity=EvidencePolarity.POSITIVE, strength=0.9)
        ctx = make_context([sig])
        assert rule.applies_to(ctx) is False

    def test_applies_when_mixed_signals(self, rule):
        pos = make_signal(polarity=EvidencePolarity.POSITIVE, strength=0.9)
        neg = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([pos, neg])
        assert rule.applies_to(ctx) is True


# --- evaluate: empty / no matching signals ---

class TestKnowledgeGapEvaluateEmpty:
    def test_returns_empty_for_high_strength_positive(self, rule):
        sig = make_signal(polarity=EvidencePolarity.POSITIVE, strength=0.9)
        ctx = make_context([sig])
        assert rule.evaluate(ctx) == []

    def test_returns_empty_when_negative_but_no_gap_criteria_high_strength(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.REPEATED_WEAKNESS,
            dimension=ProfileDimension.COMMUNICATION,
            strength=0.8,
        )
        ctx = make_context([sig])
        assert rule.evaluate(ctx) == []

    def test_returns_empty_list_type(self, rule):
        sig = make_signal(polarity=EvidencePolarity.POSITIVE, strength=0.9)
        ctx = make_context([sig])
        result = rule.evaluate(ctx)
        assert isinstance(result, list)


# --- evaluate: positive match cases ---

class TestKnowledgeGapEvaluateMatches:
    def test_detects_low_strength_negative(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1
        assert matches[0].observation_type == ObservationType.KNOWLEDGE_GAP

    def test_detects_knowledge_gap_signal_type(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.KNOWLEDGE_GAP,
            strength=0.7,
        )
        ctx = make_context([sig])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1

    def test_detects_missing_evidence_signal_type(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.MISSING_EVIDENCE,
            strength=0.6,
        )
        ctx = make_context([sig])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1

    def test_detects_shallow_answer_signal_type(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.SHALLOW_ANSWER,
            strength=0.5,
        )
        ctx = make_context([sig])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1

    def test_detects_reasoning_gap_signal_type(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            signal_type=EvidenceType.REASONING_GAP,
            strength=0.5,
        )
        ctx = make_context([sig])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1

    def test_detects_technical_depth_dimension(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            signal_type=EvidenceType.REPEATED_WEAKNESS,
            strength=0.6,
        )
        ctx = make_context([sig])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1

    def test_detects_engineering_judgment_dimension(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.ENGINEERING_JUDGMENT,
            signal_type=EvidenceType.REPEATED_WEAKNESS,
            strength=0.6,
        )
        ctx = make_context([sig])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1

    def test_multiple_dimensions_produce_multiple_matches(self, rule):
        sig1 = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            signal_type=EvidenceType.KNOWLEDGE_GAP,
            strength=0.2,
        )
        sig2 = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.PROBLEM_SOLVING,
            signal_type=EvidenceType.KNOWLEDGE_GAP,
            strength=0.2,
        )
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 2

    def test_same_dimension_aggregated_to_one_match(self, rule):
        sig1 = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.1)
        sig2 = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig1, sig2])
        matches = rule.evaluate(ctx)
        assert len(matches) == 1


# --- evaluate: match content ---

class TestKnowledgeGapMatchContent:
    def test_rule_id_in_match(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert match.rule_id == "knowledge_gap_rule"

    def test_confidence_range(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert 0.0 <= match.confidence <= 1.0

    def test_confidence_inverted_from_strength(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.1)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert match.confidence > 0.5

    def test_confidence_lower_for_higher_strength(self, rule):
        sig_low = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.1)
        sig_high = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.3)
        ctx_low = make_context([sig_low])
        ctx_high = make_context([sig_high])
        match_low = rule.evaluate(ctx_low)[0]
        match_high = rule.evaluate(ctx_high)[0]
        assert match_low.confidence >= match_high.confidence

    def test_description_non_empty(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert len(match.description) > 0

    def test_tags_include_knowledge_gap(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert "knowledge_gap" in match.tags

    def test_tags_include_dimension(self, rule):
        sig = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            strength=0.2,
        )
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert "technical_depth" in match.tags

    def test_rationale_non_empty(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert len(match.rationale) > 0


# --- Determinism & Replay ---

class TestKnowledgeGapDeterminism:
    def test_same_context_same_output(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2)
        ctx = make_context([sig])
        result1 = rule.evaluate(ctx)
        result2 = rule.evaluate(ctx)
        assert result1 == result2

    def test_multiple_calls_deterministic(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.1)
        ctx = make_context([sig])
        results = [rule.evaluate(ctx) for _ in range(5)]
        assert all(r == results[0] for r in results)

    def test_confidence_at_max_strength_zero(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.0)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert match.confidence == 1.0

    def test_confidence_at_strength_threshold(self, rule):
        sig = make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.3)
        ctx = make_context([sig])
        match = rule.evaluate(ctx)[0]
        assert 0.0 <= match.confidence <= 1.0
