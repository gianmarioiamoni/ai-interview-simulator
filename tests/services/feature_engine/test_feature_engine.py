# tests/services/feature_engine/test_feature_engine.py
# Core FeatureEngine orchestration tests

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType
from services.feature_engine.feature_engine import FeatureEngine, FeatureEngineError
from services.feature_engine.feature_engine_context import FeatureEngineContext
from tests.services.feature_engine.conftest import (
    EmptyUpdater,
    ErrorUpdater,
    PassthroughComposer,
    StubUpdater,
    make_candidate,
    make_context,
    make_observation,
    make_snapshot,
)


class TestFeatureEngineConstruction:
    def test_valid_construction(self) -> None:
        updater = StubUpdater()
        engine = FeatureEngine([updater], PassthroughComposer())
        assert engine is not None

    def test_empty_updaters_rejected(self) -> None:
        with pytest.raises(FeatureEngineError):
            FeatureEngine([], PassthroughComposer())

    def test_duplicate_updater_id_rejected(self) -> None:
        u1 = StubUpdater(updater_id="same")
        u2 = StubUpdater(updater_id="same", invocation_order=2)
        with pytest.raises(FeatureEngineError):
            FeatureEngine([u1, u2], PassthroughComposer())

    def test_registered_updater_ids(self) -> None:
        u1 = StubUpdater(updater_id="a", invocation_order=1)
        u2 = StubUpdater(updater_id="b", invocation_order=2)
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        assert set(engine.registered_updater_ids) == {"a", "b"}

    def test_engine_version_default(self) -> None:
        engine = FeatureEngine([StubUpdater()], PassthroughComposer())
        assert engine.engine_version == "1.0.0"

    def test_engine_version_custom(self) -> None:
        engine = FeatureEngine([StubUpdater()], PassthroughComposer(), engine_version="2.0.0")
        assert engine.engine_version == "2.0.0"


class TestFeatureEnginePipelineOrdering:
    """ADR-020 §D: Updaters invoked in invocation_order ASC."""

    def test_single_updater_invoked(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        engine.run(make_context())
        assert updater.produce_call_count == 1

    def test_multiple_updaters_all_invoked(self) -> None:
        u1 = StubUpdater(updater_id="a", invocation_order=1)
        u2 = StubUpdater(updater_id="b", invocation_order=2)
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        engine.run(make_context())
        assert u1.produce_call_count == 1
        assert u2.produce_call_count == 1

    def test_updaters_sorted_by_invocation_order(self) -> None:
        """Updaters registered in reverse order must still run in order."""
        invocation_trace: list[str] = []

        class TracingUpdater(StubUpdater):
            def produce(self, observations):
                invocation_trace.append(self.updater_id)
                return super().produce(observations)

        u1 = TracingUpdater(updater_id="first", invocation_order=1)
        u2 = TracingUpdater(updater_id="second", invocation_order=2)
        u3 = TracingUpdater(updater_id="third", invocation_order=3)
        # Register in reverse
        engine = FeatureEngine([u3, u1, u2], PassthroughComposer())
        engine.run(make_context())
        assert invocation_trace == ["first", "second", "third"]

    def test_plan_updater_specs_ordered(self) -> None:
        u1 = StubUpdater(updater_id="a", invocation_order=1)
        u2 = StubUpdater(updater_id="b", invocation_order=2)
        engine = FeatureEngine([u2, u1], PassthroughComposer())
        result = engine.run(make_context())
        orders = [s.invocation_order for s in result.diagnostics.plan.updater_specs]
        assert orders == sorted(orders)


class TestFeatureEnginePipeline:
    """Full five-stage pipeline correctness (ADR-020 §C, §E)."""

    def test_produces_profile_features(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate(FeatureType.REASONING)])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert len(result.features) == 1

    def test_feature_value_correct(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate(FeatureType.REASONING, "MODERATE")])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.features[0].value == "MODERATE"

    def test_candidate_identity_id_in_feature(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(candidate_id="cand-XYZ"))
        assert result.features[0].candidate_identity_id == "cand-XYZ"

    def test_feature_engine_version_in_provenance(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer(), engine_version="3.0.0")
        ctx = make_context()
        # context.feature_engine_version is passed to composer; use matching version
        ctx_versioned = FeatureEngineContext(
            session_id=ctx.session_id,
            candidate_identity_id=ctx.candidate_identity_id,
            current_question_index=ctx.current_question_index,
            snapshot=ctx.snapshot,
            feature_engine_version="3.0.0",
        )
        result = engine.run(ctx_versioned)
        assert result.features[0].provenance.feature_engine_version == "3.0.0"

    def test_empty_candidates_produces_no_features(self) -> None:
        engine = FeatureEngine([EmptyUpdater()], PassthroughComposer())
        result = engine.run(make_context())
        assert result.feature_count == 0

    def test_multiple_feature_types_from_one_updater(self) -> None:
        candidates = [
            make_candidate(FeatureType.REASONING),
            make_candidate(FeatureType.TREND),
            make_candidate(FeatureType.COVERAGE),
        ]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset({"reasoning_feature", "trend_feature", "coverage_feature"}),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.feature_count == 3

    def test_session_id_propagated_to_result(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(session_id="my-session"))
        assert result.session_id == "my-session"

    def test_question_index_propagated_to_result(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate(question_index=7)])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(question_index=7))
        assert result.current_question_index == 7

    def test_result_is_successful(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.is_successful is True


class TestFeatureEngineObservationFiltering:
    """ADR-020 §D: updaters receive only observations relevant to their type set."""

    def test_updater_receives_matching_observations(self) -> None:
        obs = make_observation(ObservationType.REASONING_DEPTH_HIGH)
        snap = make_snapshot([obs])
        updater = StubUpdater(
            observation_type_set=frozenset({"reasoning_depth_high"}),
            candidates_to_produce=[],
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        engine.run(make_context(snapshot=snap))
        assert len(updater.last_observations_received) == 1

    def test_updater_does_not_receive_non_matching_observations(self) -> None:
        obs = make_observation(ObservationType.COMMUNICATION_CLEAR)
        snap = make_snapshot([obs])
        updater = StubUpdater(
            observation_type_set=frozenset({"reasoning_depth_high"}),
            candidates_to_produce=[],
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        engine.run(make_context(snapshot=snap))
        assert len(updater.last_observations_received) == 0

    def test_wildcard_updater_receives_all_observations(self) -> None:
        obs1 = make_observation(ObservationType.REASONING_DEPTH_HIGH)
        obs2 = make_observation(ObservationType.COMMUNICATION_CLEAR)
        snap = make_snapshot([obs1, obs2])
        # Empty observation_type_set = wildcard
        updater = StubUpdater(observation_type_set=frozenset(), candidates_to_produce=[])
        engine = FeatureEngine([updater], PassthroughComposer())
        engine.run(make_context(snapshot=snap))
        assert len(updater.last_observations_received) == 2

    def test_multiple_updaters_receive_own_observations(self) -> None:
        reasoning_obs = make_observation(ObservationType.REASONING_DEPTH_HIGH)
        comm_obs = make_observation(ObservationType.COMMUNICATION_CLEAR)
        snap = make_snapshot([reasoning_obs, comm_obs])

        reasoning_updater = StubUpdater(
            updater_id="reasoning_upd",
            invocation_order=1,
            observation_type_set=frozenset({"reasoning_depth_high"}),
            candidates_to_produce=[],
        )
        comm_updater = StubUpdater(
            updater_id="comm_upd",
            invocation_order=2,
            observation_type_set=frozenset({"communication_clear"}),
            candidates_to_produce=[],
        )
        engine = FeatureEngine([reasoning_updater, comm_updater], PassthroughComposer())
        engine.run(make_context(snapshot=snap))
        assert len(reasoning_updater.last_observations_received) == 1
        assert len(comm_updater.last_observations_received) == 1


class TestFeatureEngineReplayPath:
    """ADR-020 §H: replay path only invokes replay_updater."""

    def test_replay_context_accepted(self) -> None:
        replay_updater = StubUpdater(
            updater_id="replay_updater",
            invocation_order=1,
            candidates_to_produce=[make_candidate()],
        )
        engine = FeatureEngine([replay_updater], PassthroughComposer())
        context = make_context(is_replay=True)
        result = engine.run(context)
        assert result.is_successful is True

    def test_non_replay_updater_skipped_in_replay_mode(self) -> None:
        live_updater = StubUpdater(
            updater_id="obs_updater",
            invocation_order=1,
            candidates_to_produce=[make_candidate()],
        )
        replay_updater = StubUpdater(
            updater_id="replay_updater",
            invocation_order=2,
            candidates_to_produce=[make_candidate(FeatureType.REASONING, "LOW")],
        )
        engine = FeatureEngine([live_updater, replay_updater], PassthroughComposer())
        context = make_context(is_replay=True)
        engine.run(context)
        assert live_updater.produce_call_count == 0
        assert replay_updater.produce_call_count == 1

    def test_replay_result_marks_is_replay(self) -> None:
        replay_updater = StubUpdater(
            updater_id="replay_updater",
            invocation_order=1,
            candidates_to_produce=[make_candidate()],
        )
        engine = FeatureEngine([replay_updater], PassthroughComposer())
        result = engine.run(make_context(is_replay=True))
        assert result.diagnostics.is_replay is True


class TestFeatureEngineDeterminism:
    """ADR-020 §L P-01: given same ObservationStore state, same output every time."""

    def test_same_input_same_output(self) -> None:
        obs = [
            make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=0),
            make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=1),
        ]
        snap = make_snapshot(obs)

        updater = StubUpdater(
            candidates_to_produce=[make_candidate(FeatureType.REASONING, "HIGH")],
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        ctx = make_context(snapshot=snap)

        result_a = engine.run(ctx)
        result_b = engine.run(ctx)

        assert result_a.features == result_b.features

    def test_different_observations_different_output(self) -> None:
        updater_high = StubUpdater(
            updater_id="upd_high",
            candidates_to_produce=[make_candidate(FeatureType.REASONING, "HIGH")],
        )
        updater_low = StubUpdater(
            updater_id="upd_low",
            candidates_to_produce=[make_candidate(FeatureType.REASONING, "LOW")],
        )
        engine_high = FeatureEngine([updater_high], PassthroughComposer())
        engine_low = FeatureEngine([updater_low], PassthroughComposer())

        result_high = engine_high.run(make_context())
        result_low = engine_low.run(make_context())

        assert result_high.features[0].value != result_low.features[0].value


class TestFeatureEngineDiagnosticsAndMetrics:
    """ADR-020 §K: observability model."""

    def test_metrics_in_result(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.metrics is not None

    def test_metrics_features_computed(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.metrics.features_computed == 1

    def test_metrics_candidates_collected(self) -> None:
        candidates = [make_candidate(FeatureType.REASONING), make_candidate(FeatureType.TREND)]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset({"reasoning_feature", "trend_feature"}),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.metrics.candidates_collected == 2

    def test_metrics_observation_count(self) -> None:
        obs = [make_observation(), make_observation(question_index=1)]
        snap = make_snapshot(obs)
        updater = StubUpdater(candidates_to_produce=[])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(snapshot=snap))
        assert result.diagnostics.metrics.observation_count == 2

    def test_updater_timing_records_present(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert len(result.diagnostics.metrics.updater_timings) >= 1

    def test_updater_invocation_records_present(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert len(result.diagnostics.updater_invocation_records) >= 1

    def test_resolution_report_single_candidate(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.resolution_report.single_candidate_resolutions == 1

    def test_plan_in_diagnostics(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.plan is not None

    def test_metrics_cycle_duration_non_negative(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.metrics.total_cycle_duration_ms >= 0.0


class TestFeatureEngineInvariants:
    """ADR-018 §C, ADR-020 §B: FeatureEngine never creates Observations."""

    def test_engine_does_not_create_observations(self) -> None:
        """Verifying by design: engine has no ObservationExtractor dependency."""
        import inspect
        from services.feature_engine import feature_engine as fe_module
        source = inspect.getsource(fe_module)
        assert "ObservationExtractor" not in source

    def test_engine_does_not_invoke_llm(self) -> None:
        import inspect
        from services.feature_engine import feature_engine as fe_module
        source = inspect.getsource(fe_module)
        assert "openai" not in source.lower()
        assert "anthropic" not in source.lower()

    def test_sole_producer_via_composer(self) -> None:
        """Composer is always called — no ProfileFeature is created outside it."""
        called = []

        class TrackingComposer(PassthroughComposer):
            def compose(self, candidates, cid, ver):
                called.append(True)
                return super().compose(candidates, cid, ver)

        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], TrackingComposer())
        engine.run(make_context())
        assert called

    def test_engine_result_features_are_immutable(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            result.features[0].value = "MODIFIED"  # type: ignore[misc]
