# tests/domain/contracts/observation/extraction/test_observation_extractor.py
# Core extractor behaviour: determinism, rule ordering, single writer, error isolation

import pytest

from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.extraction.observation_rule_priority import ObservationRulePriority
from domain.contracts.observation.extraction.observation_rule_registry import ObservationRuleRegistry
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from tests.domain.contracts.observation.extraction.conftest import (
    AlwaysMatchRule,
    AppliesErrorRule,
    ErrorRule,
    InMemoryObservationStore,
    MultiMatchRule,
    NeverMatchRule,
    SkipRule,
    make_context,
    make_extractor,
    make_registry,
)


class TestObservationExtractorConstruction:
    def test_requires_frozen_registry(self):
        registry = ObservationRuleRegistry()
        store = InMemoryObservationStore()
        with pytest.raises(RuntimeError):
            ObservationExtractor(registry=registry, store=store)

    def test_constructs_with_frozen_registry(self):
        extractor, _ = make_extractor()
        assert extractor is not None

    def test_session_metrics_initial_state(self):
        extractor, _ = make_extractor(AlwaysMatchRule())
        metrics = extractor.session_metrics()
        assert metrics.total_cycles == 0
        assert metrics.total_observations_produced == 0


class TestObservationExtractorSessionMismatch:
    def test_wrong_session_id_raises(self):
        extractor, _ = make_extractor(AlwaysMatchRule(), session_id="correct-session")
        ctx = make_context(session_id="wrong-session")
        with pytest.raises(ValueError):
            extractor.extract(ctx)


class TestObservationExtractorEmptyRegistry:
    def test_empty_registry_returns_empty_result(self):
        extractor, _ = make_extractor()
        ctx = make_context()
        result = extractor.extract(ctx)
        assert result.is_empty
        assert result.observation_count == 0

    def test_empty_registry_nothing_stored(self):
        extractor, store = make_extractor()
        extractor.extract(make_context())
        assert store.count() == 0


class TestObservationExtractorBasicExtraction:
    def test_always_match_produces_one_observation(self):
        extractor, _ = make_extractor(AlwaysMatchRule())
        result = extractor.extract(make_context())
        assert result.observation_count == 1

    def test_never_match_produces_no_observations(self):
        extractor, _ = make_extractor(NeverMatchRule())
        result = extractor.extract(make_context())
        assert result.is_empty

    def test_observation_appended_to_store(self):
        extractor, store = make_extractor(AlwaysMatchRule())
        extractor.extract(make_context())
        assert store.count() == 1

    def test_observation_has_evidence_signal_origin(self):
        extractor, store = make_extractor(AlwaysMatchRule())
        extractor.extract(make_context())
        snap = store.snapshot()
        assert snap.observations[0].metadata.origin == ObservationOrigin.EVIDENCE_SIGNAL

    def test_observation_status_is_active(self):
        extractor, store = make_extractor(AlwaysMatchRule())
        extractor.extract(make_context())
        snap = store.snapshot()
        assert snap.observations[0].status == ObservationStatus.ACTIVE

    def test_observation_source_ref_is_rule_id(self):
        extractor, store = make_extractor(AlwaysMatchRule(rule_id="my-rule"))
        extractor.extract(make_context())
        snap = store.snapshot()
        assert snap.observations[0].metadata.source_ref == "my-rule"

    def test_observation_extractor_version_set(self):
        extractor, store = make_extractor(AlwaysMatchRule())
        extractor.extract(make_context())
        snap = store.snapshot()
        assert snap.observations[0].metadata.extractor_version == ObservationExtractor.VERSION

    def test_multi_rule_multi_observation(self):
        extractor, store = make_extractor(
            AlwaysMatchRule(rule_id="r1"),
            AlwaysMatchRule(rule_id="r2", observation_type=ObservationType.COMMUNICATION_CLEAR),
        )
        result = extractor.extract(make_context())
        assert result.observation_count == 2
        assert store.count() == 2

    def test_multi_match_rule_produces_multiple(self):
        extractor, store = make_extractor(MultiMatchRule())
        result = extractor.extract(make_context())
        assert result.observation_count == 2

    def test_skip_rule_produces_no_observations(self):
        extractor, store = make_extractor(SkipRule())
        result = extractor.extract(make_context())
        assert result.is_empty
        assert store.count() == 0


class TestObservationExtractorDeterminism:
    def test_same_context_same_observations_twice(self):
        rule = AlwaysMatchRule(rule_id="det-rule", observation_type=ObservationType.TECHNICAL_CORRECTNESS)
        ctx = make_context(question_index=0)

        extractor1, store1 = make_extractor(rule.__class__(rule_id="det-rule"))
        result1 = extractor1.extract(ctx)

        extractor2, store2 = make_extractor(rule.__class__(rule_id="det-rule"))
        result2 = extractor2.extract(ctx)

        assert result1.observation_count == result2.observation_count
        for o1, o2 in zip(result1.observations, result2.observations):
            assert o1.observation_type == o2.observation_type
            assert o1.confidence == o2.confidence
            assert o1.description == o2.description

    def test_result_observations_ordered_deterministically(self):
        extractor, _ = make_extractor(
            MultiMatchRule(
                rule_id="multi",
                matches=[
                    (ObservationType.TECHNICAL_CORRECTNESS, 0.9),
                    (ObservationType.COMMUNICATION_CLEAR, 0.7),
                ],
            )
        )
        result1 = extractor.extract(make_context(question_index=0))
        extractor2, _ = make_extractor(
            MultiMatchRule(
                rule_id="multi",
                matches=[
                    (ObservationType.TECHNICAL_CORRECTNESS, 0.9),
                    (ObservationType.COMMUNICATION_CLEAR, 0.7),
                ],
            )
        )
        result2 = extractor2.extract(make_context(question_index=0))
        types1 = [o.observation_type for o in result1.observations]
        types2 = [o.observation_type for o in result2.observations]
        assert types1 == types2


class TestObservationExtractorRuleOrdering:
    def test_critical_rule_fires_before_normal(self):
        fired_order: list[str] = []

        class TrackRule(AlwaysMatchRule):
            def evaluate(self, context):
                fired_order.append(self.rule_id)
                return []

        extractor, _ = make_extractor(
            TrackRule(rule_id="normal-rule", priority=ObservationRulePriority.NORMAL),
            TrackRule(rule_id="critical-rule", priority=ObservationRulePriority.CRITICAL),
        )
        extractor.extract(make_context())
        assert fired_order.index("critical-rule") < fired_order.index("normal-rule")

    def test_tie_broken_by_rule_id(self):
        fired_order: list[str] = []

        class TrackRule(AlwaysMatchRule):
            def evaluate(self, context):
                fired_order.append(self.rule_id)
                return []

        extractor, _ = make_extractor(
            TrackRule(rule_id="z-rule", priority=ObservationRulePriority.NORMAL),
            TrackRule(rule_id="a-rule", priority=ObservationRulePriority.NORMAL),
            TrackRule(rule_id="m-rule", priority=ObservationRulePriority.NORMAL),
        )
        extractor.extract(make_context())
        assert fired_order == ["a-rule", "m-rule", "z-rule"]

    def test_all_priorities_ordered(self):
        fired_order: list[str] = []

        class TrackRule(AlwaysMatchRule):
            def evaluate(self, context):
                fired_order.append(self.rule_id)
                return []

        extractor, _ = make_extractor(
            TrackRule(rule_id="fallback", priority=ObservationRulePriority.FALLBACK),
            TrackRule(rule_id="critical", priority=ObservationRulePriority.CRITICAL),
            TrackRule(rule_id="low", priority=ObservationRulePriority.LOW),
            TrackRule(rule_id="high", priority=ObservationRulePriority.HIGH),
            TrackRule(rule_id="normal", priority=ObservationRulePriority.NORMAL),
        )
        extractor.extract(make_context())
        assert fired_order == ["critical", "high", "normal", "low", "fallback"]


class TestObservationExtractorErrorIsolation:
    def test_error_rule_does_not_abort_extraction(self):
        extractor, store = make_extractor(
            ErrorRule(rule_id="bad-rule"),
            AlwaysMatchRule(rule_id="good-rule"),
        )
        result = extractor.extract(make_context())
        assert result.observation_count == 1
        assert store.count() == 1

    def test_applies_to_error_skips_rule(self):
        extractor, store = make_extractor(
            AppliesErrorRule(rule_id="applies-bad"),
            AlwaysMatchRule(rule_id="good-rule"),
        )
        result = extractor.extract(make_context())
        assert result.observation_count == 1

    def test_error_recorded_in_diagnostics(self):
        extractor, _ = make_extractor(ErrorRule(rule_id="err"))
        result = extractor.extract(make_context())
        diag = result.diagnostics
        assert diag.rules_errored == 1
        assert any(d.error_message is not None for d in diag.rule_diagnostics)

    def test_applies_to_error_recorded_in_diagnostics(self):
        extractor, _ = make_extractor(AppliesErrorRule(rule_id="ae"))
        result = extractor.extract(make_context())
        assert result.diagnostics.rules_errored == 1

    def test_all_rules_error_produces_empty_result(self):
        extractor, store = make_extractor(
            ErrorRule(rule_id="e1"),
            ErrorRule(rule_id="e2"),
        )
        result = extractor.extract(make_context())
        assert result.is_empty
        assert store.count() == 0


class TestObservationExtractorDiagnostics:
    def test_diagnostics_question_index_matches(self):
        extractor, _ = make_extractor(AlwaysMatchRule())
        result = extractor.extract(make_context(question_index=7))
        assert result.diagnostics.question_index == 7

    def test_diagnostics_session_id_matches(self):
        extractor, _ = make_extractor(AlwaysMatchRule(), session_id="diag-session")
        result = extractor.extract(make_context(session_id="diag-session"))
        assert result.diagnostics.session_id == "diag-session"

    def test_skip_recorded_in_diagnostics(self):
        extractor, _ = make_extractor(SkipRule(rule_id="skip"))
        result = extractor.extract(make_context())
        assert result.diagnostics.rules_skipped == 1

    def test_evaluated_count_correct(self):
        extractor, _ = make_extractor(
            AlwaysMatchRule(rule_id="r1"),
            NeverMatchRule(rule_id="r2"),
        )
        result = extractor.extract(make_context())
        assert result.diagnostics.rules_evaluated == 2

    def test_total_matches_in_diagnostics(self):
        extractor, _ = make_extractor(MultiMatchRule())
        result = extractor.extract(make_context())
        assert result.diagnostics.total_matches == 2

    def test_rule_diagnostics_count_equals_rules(self):
        extractor, _ = make_extractor(
            AlwaysMatchRule(rule_id="r1"),
            NeverMatchRule(rule_id="r2"),
            SkipRule(rule_id="r3"),
        )
        result = extractor.extract(make_context())
        assert len(result.diagnostics.rule_diagnostics) == 3


class TestObservationExtractorMultipleCycles:
    def test_multiple_cycles_accumulate_store(self):
        extractor, store = make_extractor(AlwaysMatchRule())
        extractor.extract(make_context(question_index=0))
        extractor.extract(make_context(question_index=1))
        extractor.extract(make_context(question_index=2))
        assert store.count() == 3

    def test_metrics_cycle_count(self):
        extractor, _ = make_extractor(AlwaysMatchRule())
        for i in range(5):
            extractor.extract(make_context(question_index=i))
        assert extractor.session_metrics().total_cycles == 5

    def test_metrics_observations_produced(self):
        extractor, _ = make_extractor(AlwaysMatchRule())
        for i in range(3):
            extractor.extract(make_context(question_index=i))
        assert extractor.session_metrics().total_observations_produced == 3

    def test_metrics_rule_invocations_count(self):
        extractor, _ = make_extractor(AlwaysMatchRule(rule_id="r"))
        for i in range(4):
            extractor.extract(make_context(question_index=i))
        metrics = extractor.session_metrics()
        rule_m = next(m for m in metrics.rule_metrics if m.rule_id == "r")
        assert rule_m.invocations == 4

    def test_metrics_type_counts(self):
        extractor, _ = make_extractor(
            AlwaysMatchRule(rule_id="r", observation_type=ObservationType.TECHNICAL_CORRECTNESS)
        )
        for i in range(3):
            extractor.extract(make_context(question_index=i))
        metrics = extractor.session_metrics()
        tc = next(
            (c for c in metrics.type_counts if c.observation_type == ObservationType.TECHNICAL_CORRECTNESS),
            None,
        )
        assert tc is not None
        assert tc.count == 3


class TestObservationExtractorResultOrdering:
    def test_result_type_sorted_asc(self):
        extractor, _ = make_extractor(
            MultiMatchRule(
                rule_id="multi",
                matches=[
                    (ObservationType.TECHNICAL_CORRECTNESS, 0.9),
                    (ObservationType.COMMUNICATION_CLEAR, 0.7),
                ],
            )
        )
        result = extractor.extract(make_context())
        types = [o.observation_type.value for o in result.observations]
        assert types == sorted(types)

    def test_same_type_sorted_confidence_desc(self):
        extractor, _ = make_extractor(
            MultiMatchRule(
                rule_id="multi",
                matches=[
                    (ObservationType.TECHNICAL_CORRECTNESS, 0.3),
                    (ObservationType.TECHNICAL_CORRECTNESS, 0.9),
                    (ObservationType.TECHNICAL_CORRECTNESS, 0.6),
                ],
            )
        )
        result = extractor.extract(make_context())
        confs = [o.confidence for o in result.observations if o.observation_type == ObservationType.TECHNICAL_CORRECTNESS]
        assert confs == sorted(confs, reverse=True)
