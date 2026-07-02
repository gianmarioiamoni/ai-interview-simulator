# tests/domain/contracts/observation/extraction/test_extraction_layer_invariants.py
# Architecture invariants: ADR-016, ADR-017, ADR-021

import inspect

import pytest
from pydantic import ValidationError

from domain.contracts.observation.extraction.observation_extraction_context import ObservationExtractionContext
from domain.contracts.observation.extraction.observation_extraction_diagnostics import (
    ObservationExtractionDiagnostics,
    ObservationRuleDiagnostic,
)
from domain.contracts.observation.extraction.observation_extraction_result import ObservationExtractionResult
from domain.contracts.observation.extraction.observation_extractor import ObservationExtractor
from domain.contracts.observation.extraction.observation_extractor_metrics import (
    ObservationExtractorMetrics,
    ObservationRuleMetric,
    ObservationTypeCount,
)
from domain.contracts.observation.extraction.observation_rule import ObservationRule
from domain.contracts.observation.extraction.observation_rule_match import ObservationRuleMatch
from domain.contracts.observation.extraction.observation_rule_registry import (
    DuplicateRuleError,
    ObservationRuleRegistry,
)
from domain.contracts.observation.observation_type import ObservationType
from tests.domain.contracts.observation.extraction.conftest import (
    AlwaysMatchRule,
    InMemoryObservationStore,
    make_context,
    make_extractor,
)


class TestImmutabilityInvariant:
    """All extraction layer contracts must be frozen (ADR-016)."""

    def test_observation_rule_match_is_frozen(self):
        assert ObservationRuleMatch.model_config.get("frozen") is True

    def test_observation_extraction_context_is_frozen(self):
        assert ObservationExtractionContext.model_config.get("frozen") is True

    def test_observation_rule_diagnostic_is_frozen(self):
        assert ObservationRuleDiagnostic.model_config.get("frozen") is True

    def test_observation_extraction_diagnostics_is_frozen(self):
        assert ObservationExtractionDiagnostics.model_config.get("frozen") is True

    def test_observation_extraction_result_is_frozen(self):
        assert ObservationExtractionResult.model_config.get("frozen") is True

    def test_observation_rule_metric_is_frozen(self):
        assert ObservationRuleMetric.model_config.get("frozen") is True

    def test_observation_type_count_is_frozen(self):
        assert ObservationTypeCount.model_config.get("frozen") is True

    def test_observation_extractor_metrics_is_frozen(self):
        assert ObservationExtractorMetrics.model_config.get("frozen") is True


class TestExtraForbiddenInvariant:
    """All extraction layer contracts must have extra='forbid' (ADR-016)."""

    def test_rule_match_extra_forbid(self):
        assert ObservationRuleMatch.model_config.get("extra") == "forbid"

    def test_context_extra_forbid(self):
        assert ObservationExtractionContext.model_config.get("extra") == "forbid"

    def test_rule_diagnostic_extra_forbid(self):
        assert ObservationRuleDiagnostic.model_config.get("extra") == "forbid"

    def test_diagnostics_extra_forbid(self):
        assert ObservationExtractionDiagnostics.model_config.get("extra") == "forbid"

    def test_result_extra_forbid(self):
        assert ObservationExtractionResult.model_config.get("extra") == "forbid"

    def test_rule_metric_extra_forbid(self):
        assert ObservationRuleMetric.model_config.get("extra") == "forbid"

    def test_type_count_extra_forbid(self):
        assert ObservationTypeCount.model_config.get("extra") == "forbid"

    def test_extractor_metrics_extra_forbid(self):
        assert ObservationExtractorMetrics.model_config.get("extra") == "forbid"


class TestObservationRuleIsAbstractInvariant:
    def test_rule_is_abstract(self):
        assert inspect.isabstract(ObservationRule)

    def test_rule_abstract_methods(self):
        assert {"rule_id", "priority", "evaluate"}.issubset(ObservationRule.__abstractmethods__)


class TestSingleWriterInvariant:
    """ObservationExtractor is the ONLY writer to ObservationStore (ADR-016)."""

    def test_extractor_appends_to_store(self):
        extractor, store = make_extractor(AlwaysMatchRule())
        extractor.extract(make_context())
        assert store.count() == 1

    def test_direct_store_append_bypasses_extractor(self):
        """This is a documentation invariant — the test confirms the store
        itself has no guard (the guard is architectural, not runtime)."""
        from domain.contracts.observation.observation import Observation
        from domain.contracts.observation.observation_metadata import ObservationMetadata
        from domain.contracts.observation.observation_origin import ObservationOrigin
        from domain.contracts.observation.observation_type import ObservationType

        store = InMemoryObservationStore()
        meta = ObservationMetadata(
            question_index=0,
            session_id="test-session",
            origin=ObservationOrigin.EVIDENCE_SIGNAL,
            source_ref="direct",
        )
        obs = Observation(
            observation_type=ObservationType.TECHNICAL_CORRECTNESS,
            metadata=meta,
            description="direct write",
            confidence=0.5,
        )
        # Direct write is possible at runtime — single-writer is an architectural constraint
        store.append(obs)
        assert store.count() == 1


class TestRegistryFreezeInvariant:
    """Registry must be frozen before extractor can use it (ADR-016)."""

    def test_unfrozen_registry_rejected(self):
        registry = ObservationRuleRegistry()
        store = InMemoryObservationStore()
        with pytest.raises(RuntimeError):
            ObservationExtractor(registry=registry, store=store)

    def test_frozen_registry_accepted(self):
        registry = ObservationRuleRegistry()
        registry.freeze()
        store = InMemoryObservationStore()
        extractor = ObservationExtractor(registry=registry, store=store)
        assert extractor is not None


class TestDuplicateRuleRegistrationInvariant:
    def test_duplicate_raises_duplicate_rule_error(self):
        registry = ObservationRuleRegistry()
        registry.register(AlwaysMatchRule(rule_id="dup"))
        with pytest.raises(DuplicateRuleError):
            registry.register(AlwaysMatchRule(rule_id="dup"))

    def test_duplicate_rule_error_is_value_error(self):
        assert issubclass(DuplicateRuleError, ValueError)


class TestPluginArchitectureInvariant:
    """Rules are stateless, independent, and swappable without rebuilding the extractor."""

    def test_different_rules_produce_different_observations(self):
        extractor1, _ = make_extractor(
            AlwaysMatchRule(rule_id="r", observation_type=ObservationType.TECHNICAL_CORRECTNESS)
        )
        extractor2, _ = make_extractor(
            AlwaysMatchRule(rule_id="r", observation_type=ObservationType.LEADERSHIP_STRONG)
        )
        from domain.contracts.observation.observation_type import ObservationType as OT
        result1 = extractor1.extract(make_context())
        result2 = extractor2.extract(make_context())
        assert result1.observations[0].observation_type == OT.TECHNICAL_CORRECTNESS
        assert result2.observations[0].observation_type == OT.LEADERSHIP_STRONG

    def test_rule_state_does_not_leak_between_extractions(self):
        """Rules are stateless — multiple calls to same rule produce same output."""
        rule = AlwaysMatchRule(rule_id="stateless")
        extractor, _ = make_extractor(rule)
        result1 = extractor.extract(make_context(question_index=0))
        result2 = extractor.extract(make_context(question_index=1))
        assert result1.observations[0].confidence == result2.observations[0].confidence

    def test_registry_order_frozen_after_freeze(self):
        registry = ObservationRuleRegistry()
        registry.register(AlwaysMatchRule(rule_id="r1"))
        registry.freeze()
        order_before = [r.rule_id for r in registry.ordered_rules()]
        order_after = [r.rule_id for r in registry.ordered_rules()]
        assert order_before == order_after


class TestDeterminismInvariant:
    """Same context + same registry → same observations (ADR-016)."""

    def test_identical_contexts_produce_identical_types(self):
        extractor1, _ = make_extractor(AlwaysMatchRule(rule_id="r"))
        extractor2, _ = make_extractor(AlwaysMatchRule(rule_id="r"))
        ctx = make_context(question_index=3)
        r1 = extractor1.extract(ctx)
        r2 = extractor2.extract(ctx)
        assert [o.observation_type for o in r1.observations] == [o.observation_type for o in r2.observations]

    def test_identical_contexts_produce_identical_confidences(self):
        extractor1, _ = make_extractor(AlwaysMatchRule(rule_id="r", confidence=0.85))
        extractor2, _ = make_extractor(AlwaysMatchRule(rule_id="r", confidence=0.85))
        ctx = make_context()
        r1 = extractor1.extract(ctx)
        r2 = extractor2.extract(ctx)
        assert r1.observations[0].confidence == r2.observations[0].confidence
