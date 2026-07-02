# tests/services/feature_engine/test_feature_engine_failure_handling.py
# Failure handling, resilience, and error propagation tests

import pytest

from domain.contracts.feature.feature_type import FeatureType
from services.feature_engine.feature_engine import FeatureEngine, FeatureEngineError
from services.feature_engine.incremental_feature_engine import IncrementalFeatureEngine
from services.feature_engine.replay_feature_engine import ReplayFeatureEngine
from tests.services.feature_engine.conftest import (
    EmptyUpdater,
    ErrorUpdater,
    PassthroughComposer,
    StubUpdater,
    make_candidate,
    make_context,
)


class TestFeatureEngineRegistryValidation:
    def test_empty_updater_list_raises(self) -> None:
        with pytest.raises(FeatureEngineError, match="requires at least one"):
            FeatureEngine([], PassthroughComposer())

    def test_duplicate_updater_ids_raises(self) -> None:
        u1 = StubUpdater(updater_id="dup")
        u2 = StubUpdater(updater_id="dup", invocation_order=2)
        with pytest.raises(FeatureEngineError, match="Duplicate"):
            FeatureEngine([u1, u2], PassthroughComposer())

    def test_three_updaters_with_dup_raises(self) -> None:
        u1 = StubUpdater(updater_id="a", invocation_order=1)
        u2 = StubUpdater(updater_id="b", invocation_order=2)
        u3 = StubUpdater(updater_id="a", invocation_order=3)
        with pytest.raises(FeatureEngineError):
            FeatureEngine([u1, u2, u3], PassthroughComposer())


class TestUpdaterExceptionPropagation:
    def test_updater_exception_propagates(self) -> None:
        """By default, exceptions from Updaters propagate to the caller."""
        engine = FeatureEngine([ErrorUpdater()], PassthroughComposer())
        with pytest.raises(RuntimeError, match="Simulated updater failure"):
            engine.run(make_context())

    def test_second_updater_runs_even_if_first_empty(self) -> None:
        u1 = EmptyUpdater(order=1)
        u2 = StubUpdater(
            updater_id="second",
            invocation_order=2,
            candidates_to_produce=[make_candidate(FeatureType.TREND)],
        )
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        result = engine.run(make_context())
        assert result.is_successful is True
        assert result.feature_count == 1


class TestIncrementalEngineFailureHandling:
    def test_replay_context_raises_clear_error(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = IncrementalFeatureEngine([updater], PassthroughComposer())
        with pytest.raises(FeatureEngineError, match="replay"):
            engine.run(make_context(is_replay=True))

    def test_reset_after_exception_allows_recovery(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = IncrementalFeatureEngine([updater], PassthroughComposer())
        engine.run(make_context(question_index=0))
        engine.reset_cache()
        result = engine.run(make_context(question_index=1))
        assert result.is_successful is True


class TestReplayEngineFailureHandling:
    def test_no_replay_updater_raises(self) -> None:
        u = StubUpdater(updater_id="obs_updater")
        with pytest.raises(FeatureEngineError, match="replay_updater"):
            ReplayFeatureEngine([u], PassthroughComposer())

    def test_live_context_raises_clear_error(self) -> None:
        u = StubUpdater(updater_id="replay_updater", candidates_to_produce=[make_candidate()])
        engine = ReplayFeatureEngine([u], PassthroughComposer())
        with pytest.raises(FeatureEngineError, match="is_replay"):
            engine.run(make_context(is_replay=False))

    def test_live_context_in_comparison_raises(self) -> None:
        u = StubUpdater(updater_id="replay_updater", candidates_to_produce=[make_candidate()])
        engine = ReplayFeatureEngine([u], PassthroughComposer())
        with pytest.raises(FeatureEngineError):
            engine.run_with_comparison(make_context(is_replay=False), ())


class TestEngineVersionPropagation:
    def test_engine_version_in_registered_property(self) -> None:
        engine = FeatureEngine([StubUpdater()], PassthroughComposer(), engine_version="2.0.1")
        assert engine.engine_version == "2.0.1"

    def test_context_engine_version_used_for_provenance(self) -> None:
        from services.feature_engine.feature_engine_context import FeatureEngineContext
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        snap = make_context().snapshot
        ctx = FeatureEngineContext(
            session_id="s",
            candidate_identity_id="c",
            current_question_index=0,
            snapshot=snap,
            feature_engine_version="9.9.9",
        )
        result = engine.run(ctx)
        assert result.features[0].provenance.feature_engine_version == "9.9.9"
