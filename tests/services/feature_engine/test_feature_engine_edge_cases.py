# tests/services/feature_engine/test_feature_engine_edge_cases.py
# Edge cases, failure handling, and ADR invariant verification

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_type import ObservationType
from services.feature_engine.feature_engine import FeatureEngine, FeatureEngineError
from tests.services.feature_engine.conftest import (
    EmptyUpdater,
    PassthroughComposer,
    StubUpdater,
    make_candidate,
    make_context,
    make_observation,
    make_snapshot,
)


class TestEdgeCasesEmptyObservations:
    def test_empty_snapshot_no_error(self) -> None:
        updater = StubUpdater(candidates_to_produce=[])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.is_successful is True
        assert result.feature_count == 0

    def test_empty_candidates_metrics_reflect_zero(self) -> None:
        engine = FeatureEngine([EmptyUpdater()], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.metrics.candidates_collected == 0
        assert result.diagnostics.metrics.features_computed == 0

    def test_large_observation_count_no_error(self) -> None:
        obs = [
            make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=i)
            for i in range(50)
        ]
        snap = make_snapshot(obs)
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(snapshot=snap))
        assert result.is_successful is True


class TestEdgeCasesMultipleUpdatersSameType:
    def test_two_updaters_same_feature_type_first_wins(self) -> None:
        """PassthroughComposer uses first-wins; both candidates collected."""
        c1 = make_candidate(FeatureType.REASONING, "HIGH", updater_id="upd1")
        c2 = make_candidate(FeatureType.REASONING, "LOW", updater_id="upd2")
        u1 = StubUpdater(
            updater_id="upd1",
            invocation_order=1,
            candidates_to_produce=[c1],
            feature_identity_set=frozenset({"reasoning_feature"}),
        )
        u2 = StubUpdater(
            updater_id="upd2",
            invocation_order=2,
            candidates_to_produce=[c2],
            feature_identity_set=frozenset({"reasoning_feature"}),
        )
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        result = engine.run(make_context())
        assert result.feature_count == 1
        assert result.diagnostics.metrics.candidates_collected == 2

    def test_all_eleven_feature_types_produced(self) -> None:
        candidates = [make_candidate(ft) for ft in FeatureType]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset(ft.value for ft in FeatureType),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.feature_count == 11


class TestEdgeCasesContextVariants:
    def test_question_index_zero(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate(question_index=0)])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(question_index=0))
        assert result.current_question_index == 0

    def test_high_question_index(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate(question_index=100)])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(question_index=100))
        assert result.current_question_index == 100

    def test_different_sessions_independent(self) -> None:
        c_a = make_candidate(FeatureType.REASONING, "HIGH")
        c_b = make_candidate(FeatureType.REASONING, "LOW")
        upd_a = StubUpdater(updater_id="upd_a", candidates_to_produce=[c_a])
        upd_b = StubUpdater(updater_id="upd_b", candidates_to_produce=[c_b])
        engine_a = FeatureEngine([upd_a], PassthroughComposer())
        engine_b = FeatureEngine([upd_b], PassthroughComposer())
        result_a = engine_a.run(make_context(session_id="sess-A"))
        result_b = engine_b.run(make_context(session_id="sess-B"))
        assert result_a.session_id == "sess-A"
        assert result_b.session_id == "sess-B"
        assert result_a.features[0].value != result_b.features[0].value


class TestEdgeCasesUpdatePlanContent:
    def test_plan_contains_all_updater_ids(self) -> None:
        u1 = StubUpdater(updater_id="a", invocation_order=1)
        u2 = StubUpdater(updater_id="b", invocation_order=2)
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        result = engine.run(make_context())
        plan_ids = {s.updater_id for s in result.diagnostics.plan.updater_specs}
        assert "a" in plan_ids
        assert "b" in plan_ids

    def test_plan_session_id_matches_context(self) -> None:
        updater = StubUpdater()
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(session_id="session-XYZ"))
        assert result.diagnostics.plan.session_id == "session-XYZ"

    def test_plan_is_full_recomputation_by_default(self) -> None:
        updater = StubUpdater()
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.diagnostics.plan.is_full_recomputation is True

    def test_plan_is_not_replay_for_live_context(self) -> None:
        updater = StubUpdater()
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(is_replay=False))
        assert result.diagnostics.plan.is_replay is False


class TestADRInvariantsAtRuntime:
    """ADR-020 §B: FeatureEngine never produces Observations."""

    def test_result_contains_no_observations(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        # FeatureEngineResult has only features, not Observations
        assert not hasattr(result, "observations")

    def test_engine_never_writes_to_snapshot(self) -> None:
        snap = make_snapshot()
        original_count = snap.total_count
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        engine.run(make_context(snapshot=snap))
        assert snap.total_count == original_count  # snapshot unchanged

    def test_provenance_observation_ids_come_from_candidate(self) -> None:
        candidate = make_candidate(obs_ids=("obs-abc", "obs-def"))
        updater = StubUpdater(candidates_to_produce=[candidate])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        obs_ids = result.features[0].provenance.source_observation_ids
        assert "obs-abc" in obs_ids
        assert "obs-def" in obs_ids

    def test_candidate_identity_id_correct_in_all_features(self) -> None:
        candidates = [make_candidate(ft) for ft in list(FeatureType)[:5]]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset(ft.value for ft in list(FeatureType)[:5]),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(candidate_id="target-candidate"))
        for feature in result.features:
            assert feature.candidate_identity_id == "target-candidate"

    def test_feature_type_ids_are_language_independent(self) -> None:
        forbidden = {"python", "java", "javascript", "typescript"}
        candidates = [make_candidate(ft) for ft in FeatureType]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset(ft.value for ft in FeatureType),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        for feature in result.features:
            for lang in forbidden:
                assert lang not in feature.feature_identity.feature_type_id.lower()


class TestPublicAPI:
    def test_all_required_symbols_exported(self) -> None:
        import services.feature_engine as pkg
        required = [
            "FeatureEngineContext",
            "FeatureEngineResult",
            "FeatureEngineMetrics",
            "FeatureEngineDiagnostics",
            "FeatureResolutionReport",
            "FeatureUpdatePlan",
            "FeatureEngine",
            "FeatureEngineError",
            "IncrementalFeatureEngine",
            "ReplayFeatureEngine",
            "UpdaterInvocationSpec",
            "ResolutionStrategy",
        ]
        for symbol in required:
            assert hasattr(pkg, symbol), f"Missing public export: {symbol}"
