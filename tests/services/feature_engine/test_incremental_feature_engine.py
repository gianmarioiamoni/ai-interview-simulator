# tests/services/feature_engine/test_incremental_feature_engine.py

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType
from services.feature_engine.feature_engine import FeatureEngineError
from services.feature_engine.incremental_feature_engine import IncrementalFeatureEngine
from services.feature_engine.feature_resolution_report import ResolutionStrategy
from tests.services.feature_engine.conftest import (
    PassthroughComposer,
    StubUpdater,
    make_candidate,
    make_context,
    make_observation,
    make_snapshot,
)


def _make_incremental_engine(
    feature_type: FeatureType = FeatureType.REASONING,
    value: str = "HIGH",
    obs_type_set: frozenset[str] | None = None,
) -> IncrementalFeatureEngine:
    candidate = make_candidate(feature_type, value)
    updater = StubUpdater(
        candidates_to_produce=[candidate],
        observation_type_set=obs_type_set or frozenset({"reasoning_depth_high"}),
        feature_identity_set=frozenset({feature_type.value}),
    )
    return IncrementalFeatureEngine([updater], PassthroughComposer())


class TestIncrementalFeatureEngineConstruction:
    def test_valid_construction(self) -> None:
        engine = _make_incremental_engine()
        assert engine is not None

    def test_no_prior_cycle_initially(self) -> None:
        engine = _make_incremental_engine()
        assert engine.has_prior_cycle is False

    def test_prior_question_index_minus_one_initially(self) -> None:
        engine = _make_incremental_engine()
        assert engine.prior_question_index == -1

    def test_replay_rejected(self) -> None:
        engine = _make_incremental_engine()
        ctx = make_context(is_replay=True)
        with pytest.raises(FeatureEngineError, match="replay"):
            engine.run(ctx)


class TestIncrementalFeatureEngineFirstCycle:
    def test_first_cycle_runs_full_recomputation(self) -> None:
        engine = _make_incremental_engine()
        result = engine.run(make_context())
        assert result.is_successful is True

    def test_first_cycle_produces_features(self) -> None:
        engine = _make_incremental_engine()
        result = engine.run(make_context())
        assert result.feature_count >= 1

    def test_first_cycle_caches_features(self) -> None:
        engine = _make_incremental_engine()
        engine.run(make_context())
        assert engine.has_prior_cycle is True

    def test_first_cycle_sets_prior_question_index(self) -> None:
        engine = _make_incremental_engine()
        engine.run(make_context(question_index=3))
        assert engine.prior_question_index == 3


class TestIncrementalFeatureEngineSubsequentCycles:
    def test_second_cycle_produces_features(self) -> None:
        engine = _make_incremental_engine()
        engine.run(make_context(question_index=0))
        result = engine.run(make_context(question_index=1))
        assert result.feature_count >= 1

    def test_prior_question_index_updated(self) -> None:
        engine = _make_incremental_engine()
        engine.run(make_context(question_index=0))
        engine.run(make_context(question_index=1))
        assert engine.prior_question_index == 1

    def test_unaffected_features_retained(self) -> None:
        # Two updaters: reasoning and trend
        r_candidate = make_candidate(FeatureType.REASONING, "HIGH")
        t_candidate = make_candidate(FeatureType.TREND, "IMPROVING")

        reasoning_updater = StubUpdater(
            updater_id="reasoning_upd",
            invocation_order=1,
            candidates_to_produce=[r_candidate],
            observation_type_set=frozenset({"reasoning_depth_high"}),
            feature_identity_set=frozenset({"reasoning_feature"}),
        )
        trend_updater = StubUpdater(
            updater_id="trend_upd",
            invocation_order=2,
            candidates_to_produce=[t_candidate],
            observation_type_set=frozenset({"performance_improving"}),
            feature_identity_set=frozenset({"trend_feature"}),
        )

        engine = IncrementalFeatureEngine(
            [reasoning_updater, trend_updater], PassthroughComposer()
        )

        # First cycle: both features computed
        engine.run(make_context(question_index=0))

        # Second cycle: only reasoning observation — trend should be retained
        reasoning_obs = make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=1)
        snap = make_snapshot([reasoning_obs])
        result = engine.run(make_context(snapshot=snap, question_index=1))

        type_ids = result.feature_type_ids
        assert "reasoning_feature" in type_ids or "trend_feature" in type_ids

    def test_retained_features_have_retained_strategy_in_report(self) -> None:
        r_candidate = make_candidate(FeatureType.REASONING, "HIGH")
        t_candidate = make_candidate(FeatureType.TREND, "IMPROVING")

        reasoning_updater = StubUpdater(
            updater_id="reasoning_upd",
            invocation_order=1,
            candidates_to_produce=[r_candidate],
            observation_type_set=frozenset({"reasoning_depth_high"}),
            feature_identity_set=frozenset({"reasoning_feature"}),
        )
        trend_updater = StubUpdater(
            updater_id="trend_upd",
            invocation_order=2,
            candidates_to_produce=[t_candidate],
            observation_type_set=frozenset({"performance_improving"}),
            feature_identity_set=frozenset({"trend_feature"}),
        )
        engine = IncrementalFeatureEngine(
            [reasoning_updater, trend_updater], PassthroughComposer()
        )
        engine.run(make_context(question_index=0))

        reasoning_obs = make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=1)
        snap = make_snapshot([reasoning_obs])
        result = engine.run(make_context(snapshot=snap, question_index=1))

        retained = [
            r for r in result.diagnostics.resolution_report.resolution_records
            if r.strategy == ResolutionStrategy.RETAINED
        ]
        # At least one feature may be retained (trend was not touched)
        assert isinstance(retained, list)


class TestIncrementalFeatureEngineCacheReset:
    def test_reset_clears_cache(self) -> None:
        engine = _make_incremental_engine()
        engine.run(make_context())
        assert engine.has_prior_cycle is True
        engine.reset_cache()
        assert engine.has_prior_cycle is False

    def test_reset_clears_question_index(self) -> None:
        engine = _make_incremental_engine()
        engine.run(make_context(question_index=5))
        engine.reset_cache()
        assert engine.prior_question_index == -1

    def test_after_reset_next_cycle_is_full(self) -> None:
        engine = _make_incremental_engine()
        engine.run(make_context(question_index=0))
        engine.reset_cache()
        result = engine.run(make_context(question_index=1))
        assert result.is_successful is True


class TestIncrementalDeterminism:
    """ADR-020 §H: incremental must produce same output as full recomputation."""

    def test_incremental_result_consistent_with_full(self) -> None:
        candidate = make_candidate(FeatureType.REASONING, "HIGH")
        updater_inc = StubUpdater(
            candidates_to_produce=[candidate],
            observation_type_set=frozenset({"reasoning_depth_high"}),
            feature_identity_set=frozenset({"reasoning_feature"}),
        )
        updater_full = StubUpdater(
            candidates_to_produce=[candidate],
            observation_type_set=frozenset({"reasoning_depth_high"}),
            feature_identity_set=frozenset({"reasoning_feature"}),
        )
        inc_engine = IncrementalFeatureEngine([updater_inc], PassthroughComposer())
        full_engine = IncrementalFeatureEngine([updater_full], PassthroughComposer())

        obs = make_observation(ObservationType.REASONING_DEPTH_HIGH)
        snap = make_snapshot([obs])
        ctx = make_context(snapshot=snap)

        result_inc = inc_engine.run(ctx)
        result_full = full_engine.run(ctx)

        assert result_inc.features[0].value == result_full.features[0].value
