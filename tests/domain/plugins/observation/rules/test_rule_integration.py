# tests/domain/plugins/observation/rules/test_rule_integration.py

import pytest

from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.extraction.observation_rule_registry import ObservationRuleRegistry, DuplicateRuleError
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.plugins.observation.rules.behavioral_growth_observation_rule import BehavioralGrowthObservationRule
from domain.plugins.observation.rules.knowledge_gap_observation_rule import KnowledgeGapObservationRule
from domain.plugins.observation.rules.reasoning_trend_observation_rule import ReasoningTrendObservationRule
from domain.plugins.observation.rules.repeated_strength_observation_rule import RepeatedStrengthObservationRule
from domain.plugins.observation.rules.repeated_weakness_observation_rule import RepeatedWeaknessObservationRule
from tests.domain.plugins.observation.rules.conftest import make_context, make_signal


@pytest.fixture
def all_rules():
    return [
        KnowledgeGapObservationRule(),
        RepeatedStrengthObservationRule(),
        RepeatedWeaknessObservationRule(),
        ReasoningTrendObservationRule(),
        BehavioralGrowthObservationRule(),
    ]


@pytest.fixture
def frozen_registry(all_rules):
    registry = ObservationRuleRegistry()
    for rule in all_rules:
        registry.register(rule)
    registry.freeze()
    return registry


# --- Registry registration ---

class TestRegistryRegistration:
    def test_all_rules_register(self, frozen_registry):
        assert frozen_registry.rule_count() == 5

    def test_all_rule_ids_present(self, frozen_registry):
        ids = frozen_registry.rule_ids()
        assert "knowledge_gap_rule" in ids
        assert "repeated_strength_rule" in ids
        assert "repeated_weakness_rule" in ids
        assert "reasoning_trend_rule" in ids
        assert "behavioral_growth_rule" in ids

    def test_registry_is_frozen(self, frozen_registry):
        assert frozen_registry.is_frozen()

    def test_duplicate_rule_raises(self):
        registry = ObservationRuleRegistry()
        registry.register(KnowledgeGapObservationRule())
        with pytest.raises(DuplicateRuleError):
            registry.register(KnowledgeGapObservationRule())

    def test_get_by_rule_id(self, frozen_registry):
        rule = frozen_registry.get("knowledge_gap_rule")
        assert rule is not None
        assert rule.rule_id == "knowledge_gap_rule"

    def test_get_unknown_rule_id_returns_none(self, frozen_registry):
        assert frozen_registry.get("nonexistent_rule") is None


# --- Priority ordering ---

class TestRuleOrdering:
    def test_high_priority_rules_before_normal(self, frozen_registry):
        ordered = frozen_registry.ordered_rules()
        rule_ids = [r.rule_id for r in ordered]
        high_indices = [i for i, r in enumerate(ordered) if r.priority == ObservationRulePriority.HIGH]
        normal_indices = [i for i, r in enumerate(ordered) if r.priority == ObservationRulePriority.NORMAL]
        assert all(h < n for h in high_indices for n in normal_indices)

    def test_normal_priority_before_low(self, frozen_registry):
        ordered = frozen_registry.ordered_rules()
        normal_indices = [i for i, r in enumerate(ordered) if r.priority == ObservationRulePriority.NORMAL]
        low_indices = [i for i, r in enumerate(ordered) if r.priority == ObservationRulePriority.LOW]
        assert all(n < lo for n in normal_indices for lo in low_indices)

    def test_high_priority_rules_by_priority(self, frozen_registry):
        high_rules = frozen_registry.rules_by_priority(ObservationRulePriority.HIGH)
        assert len(high_rules) == 2
        ids = {r.rule_id for r in high_rules}
        assert "knowledge_gap_rule" in ids
        assert "reasoning_trend_rule" in ids

    def test_normal_priority_rules_by_priority(self, frozen_registry):
        normal_rules = frozen_registry.rules_by_priority(ObservationRulePriority.NORMAL)
        assert len(normal_rules) == 2
        ids = {r.rule_id for r in normal_rules}
        assert "repeated_strength_rule" in ids
        assert "repeated_weakness_rule" in ids

    def test_low_priority_rules_by_priority(self, frozen_registry):
        low_rules = frozen_registry.rules_by_priority(ObservationRulePriority.LOW)
        assert len(low_rules) == 1
        assert low_rules[0].rule_id == "behavioral_growth_rule"

    def test_tie_breaking_lexicographic(self, frozen_registry):
        normal_rules = frozen_registry.rules_by_priority(ObservationRulePriority.NORMAL)
        rule_ids = [r.rule_id for r in normal_rules]
        assert rule_ids == sorted(rule_ids)

    def test_ordered_rules_is_tuple(self, frozen_registry):
        assert isinstance(frozen_registry.ordered_rules(), tuple)


# --- Conflict scenarios ---

class TestConflictScenarios:
    def test_knowledge_gap_and_repeated_weakness_can_both_fire(self, frozen_registry):
        """Negative signals on same dimension can trigger both rules."""
        sig1 = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            signal_type=EvidenceType.KNOWLEDGE_GAP,
            strength=0.2,
        )
        sig2 = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            signal_type=EvidenceType.SHALLOW_ANSWER,
            strength=0.3,
        )
        ctx = make_context([sig1, sig2])
        all_matches = []
        for rule in frozen_registry.ordered_rules():
            if rule.applies_to(ctx):
                all_matches.extend(rule.evaluate(ctx))
        obs_types = {m.observation_type for m in all_matches}
        assert ObservationType.KNOWLEDGE_GAP in obs_types
        assert ObservationType.TECHNICAL_SHALLOW in obs_types

    def test_strength_and_gap_can_coexist_across_dimensions(self, frozen_registry):
        pos = make_signal(
            polarity=EvidencePolarity.POSITIVE,
            dimension=ProfileDimension.PROBLEM_SOLVING,
            strength=0.9,
        )
        pos2 = make_signal(
            polarity=EvidencePolarity.POSITIVE,
            dimension=ProfileDimension.PROBLEM_SOLVING,
            strength=0.85,
        )
        neg = make_signal(
            polarity=EvidencePolarity.NEGATIVE,
            dimension=ProfileDimension.TECHNICAL_DEPTH,
            signal_type=EvidenceType.KNOWLEDGE_GAP,
            strength=0.2,
        )
        ctx = make_context([pos, pos2, neg])
        all_matches = []
        for rule in frozen_registry.ordered_rules():
            if rule.applies_to(ctx):
                all_matches.extend(rule.evaluate(ctx))
        obs_types = {m.observation_type for m in all_matches}
        assert ObservationType.TECHNICAL_STRENGTH in obs_types
        assert ObservationType.KNOWLEDGE_GAP in obs_types

    def test_each_match_has_valid_rule_id(self, frozen_registry):
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.2),
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.25),
        ]
        ctx = make_context(sigs)
        for rule in frozen_registry.ordered_rules():
            if rule.applies_to(ctx):
                for match in rule.evaluate(ctx):
                    assert match.rule_id == rule.rule_id


# --- Replay compatibility ---

class TestReplayCompatibility:
    def test_all_rules_deterministic_for_same_context(self, frozen_registry):
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.2),
            make_signal(polarity=EvidencePolarity.POSITIVE, dimension=ProfileDimension.PROBLEM_SOLVING, strength=0.8),
            make_signal(polarity=EvidencePolarity.POSITIVE, dimension=ProfileDimension.PROBLEM_SOLVING, strength=0.75),
        ]
        ctx = make_context(sigs)
        results_1 = [
            (rule.rule_id, rule.evaluate(ctx))
            for rule in frozen_registry.ordered_rules()
            if rule.applies_to(ctx)
        ]
        results_2 = [
            (rule.rule_id, rule.evaluate(ctx))
            for rule in frozen_registry.ordered_rules()
            if rule.applies_to(ctx)
        ]
        assert results_1 == results_2

    def test_same_session_same_output_multiple_replays(self, frozen_registry):
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.15),
            make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2),
        ]
        ctx = make_context(sigs, session_id="replay-session-99")
        all_runs = [
            [m for rule in frozen_registry.ordered_rules() if rule.applies_to(ctx) for m in rule.evaluate(ctx)]
            for _ in range(5)
        ]
        assert all(run == all_runs[0] for run in all_runs)

    def test_confidence_values_are_in_range_for_all_matches(self, frozen_registry):
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.2),
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.25),
            make_signal(polarity=EvidencePolarity.POSITIVE, dimension=ProfileDimension.PROBLEM_SOLVING, strength=0.8),
            make_signal(polarity=EvidencePolarity.POSITIVE, dimension=ProfileDimension.PROBLEM_SOLVING, strength=0.75),
        ]
        ctx = make_context(sigs)
        for rule in frozen_registry.ordered_rules():
            if rule.applies_to(ctx):
                for match in rule.evaluate(ctx):
                    assert 0.0 <= match.confidence <= 1.0

    def test_schema_version_default_in_matches(self, frozen_registry):
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.2),
            make_signal(polarity=EvidencePolarity.NEGATIVE, strength=0.15),
        ]
        ctx = make_context(sigs)
        for rule in frozen_registry.ordered_rules():
            if rule.applies_to(ctx):
                for match in rule.evaluate(ctx):
                    assert match.schema_version == "1.0"

    def test_all_rules_independent(self, all_rules):
        """Each rule produces same output regardless of other rules."""
        sigs = [
            make_signal(polarity=EvidencePolarity.NEGATIVE, dimension=ProfileDimension.TECHNICAL_DEPTH, strength=0.2),
            make_signal(polarity=EvidencePolarity.POSITIVE, dimension=ProfileDimension.PROBLEM_SOLVING, strength=0.9),
        ]
        ctx = make_context(sigs)
        for rule in all_rules:
            result_a = rule.evaluate(ctx)
            result_b = rule.evaluate(ctx)
            assert result_a == result_b

    def test_register_after_freeze_raises(self, frozen_registry):
        with pytest.raises(RuntimeError):
            frozen_registry.register(KnowledgeGapObservationRule())
