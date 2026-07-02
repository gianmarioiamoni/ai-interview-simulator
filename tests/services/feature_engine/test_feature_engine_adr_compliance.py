# tests/services/feature_engine/test_feature_engine_adr_compliance.py
# ADR-018 and ADR-020 compliance tests for the FeatureEngine orchestration layer

import pytest

from domain.contracts.feature.feature_type import FeatureType
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from services.feature_engine.feature_engine import FeatureEngine, FeatureEngineError
from services.feature_engine.incremental_feature_engine import IncrementalFeatureEngine
from services.feature_engine.replay_feature_engine import ReplayFeatureEngine
from tests.services.feature_engine.conftest import (
    EmptyUpdater,
    PassthroughComposer,
    StubUpdater,
    make_candidate,
    make_context,
    make_observation,
    make_snapshot,
)


class TestADR018SoleProducer:
    """ADR-018 §C, §E: FeatureEngine is the sole producer of ProfileFeatures."""

    def test_sole_producer_via_composer_only(self) -> None:
        """ProfileFeatures must only come from composer.compose(), never created elsewhere."""
        compose_calls: list[int] = []

        class TrackingComposer(PassthroughComposer):
            def compose(self, candidates, cid, ver):
                compose_calls.append(len(candidates))
                return super().compose(candidates, cid, ver)

        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], TrackingComposer())
        result = engine.run(make_context())
        # Composer was called exactly once per run
        assert len(compose_calls) == 1
        # Features match what composer produced
        assert result.feature_count == 1

    def test_profile_features_have_provenance(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        for pf in result.features:
            assert pf.provenance is not None

    def test_provenance_links_to_source_observations(self) -> None:
        candidate = make_candidate(obs_ids=("obs-111", "obs-222"))
        updater = StubUpdater(candidates_to_produce=[candidate])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        pf = result.features[0]
        assert "obs-111" in pf.provenance.source_observation_ids
        assert "obs-222" in pf.provenance.source_observation_ids

    def test_provenance_carries_feature_engine_version(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        pf = result.features[0]
        assert pf.provenance.feature_engine_version != ""

    def test_all_features_have_candidate_identity_id(self) -> None:
        candidates = [make_candidate(ft) for ft in list(FeatureType)[:3]]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset(ft.value for ft in list(FeatureType)[:3]),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context(candidate_id="c-99"))
        for pf in result.features:
            assert pf.candidate_identity_id == "c-99"


class TestADR018SchemaVersioning:
    """ADR-018 §G: schema_version travels with every ProfileFeature."""

    def test_schema_version_present_on_all_features(self) -> None:
        candidates = [make_candidate(ft) for ft in FeatureType]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset(ft.value for ft in FeatureType),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        for pf in result.features:
            assert pf.schema_version is not None
            assert len(pf.schema_version) > 0

    def test_schema_version_matches_default(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        assert result.features[0].schema_version == "1.0"


class TestADR020FeatureIdentityStability:
    """ADR-020 §F: FeatureIdentity is stable across schema versions."""

    def test_feature_type_ids_match_registered_taxonomy(self) -> None:
        candidates = [make_candidate(ft) for ft in FeatureType]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset(ft.value for ft in FeatureType),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        produced_ids = result.feature_type_ids
        for ft in FeatureType:
            assert ft.value in produced_ids

    def test_feature_identities_are_immutable_in_result(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            result.features[0].feature_identity.feature_type_id = "modified"  # type: ignore[misc]


class TestADR020UpdaterIsolation:
    """ADR-020 §D: Updaters are independent; they cannot read each other's candidates."""

    def test_updaters_receive_identical_observation_lists(self) -> None:
        obs = [make_observation(ObservationType.REASONING_DEPTH_HIGH)]
        snap = make_snapshot(obs)

        u1 = StubUpdater(updater_id="u1", invocation_order=1, observation_type_set=frozenset())
        u2 = StubUpdater(updater_id="u2", invocation_order=2, observation_type_set=frozenset())
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        engine.run(make_context(snapshot=snap))

        assert len(u1.last_observations_received) == len(u2.last_observations_received)

    def test_updater_a_output_not_passed_to_updater_b(self) -> None:
        """u2 should not see u1's FeatureCandidates in its observations list."""
        u1_candidate = make_candidate(FeatureType.REASONING, "HIGH", updater_id="u1")
        u1 = StubUpdater(
            updater_id="u1",
            invocation_order=1,
            candidates_to_produce=[u1_candidate],
            observation_type_set=frozenset(),
        )

        received_types: list[str] = []

        class InspectingUpdater(StubUpdater):
            def produce(self, observations):
                for o in observations:
                    received_types.append(type(o).__name__)
                return []

        u2 = InspectingUpdater(
            updater_id="u2",
            invocation_order=2,
            observation_type_set=frozenset(),
        )
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        engine.run(make_context())
        # u2 should have received Observation objects, NOT FeatureCandidate objects
        assert "FeatureCandidate" not in received_types


class TestADR020PipelineSinglePass:
    """ADR-020 §L P-02: ObservationStore queried once per cycle."""

    def test_each_updater_receives_same_snapshot_observations(self) -> None:
        obs = [
            make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=0),
            make_observation(ObservationType.REASONING_DEPTH_HIGH, question_index=1),
        ]
        snap = make_snapshot(obs)
        u1 = StubUpdater(updater_id="u1", invocation_order=1, observation_type_set=frozenset())
        u2 = StubUpdater(updater_id="u2", invocation_order=2, observation_type_set=frozenset())
        engine = FeatureEngine([u1, u2], PassthroughComposer())
        engine.run(make_context(snapshot=snap))
        assert len(u1.last_observations_received) == 2
        assert len(u2.last_observations_received) == 2

    def test_producer_called_once_per_updater_per_cycle(self) -> None:
        u1 = StubUpdater(updater_id="u1", invocation_order=1)
        engine = FeatureEngine([u1], PassthroughComposer())
        engine.run(make_context())
        engine.run(make_context())
        assert u1.produce_call_count == 2


class TestADR020LanguageIndependence:
    """ADR-018 §L, ADR-020 §M: FeatureEngine is language-independent."""

    def test_no_language_name_in_feature_type_ids(self) -> None:
        forbidden = {"python", "java", "javascript", "typescript", "go", "rust"}
        candidates = [make_candidate(ft) for ft in FeatureType]
        updater = StubUpdater(
            candidates_to_produce=candidates,
            feature_identity_set=frozenset(ft.value for ft in FeatureType),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        for pf in result.features:
            for lang in forbidden:
                assert lang not in pf.feature_identity.feature_type_id.lower()

    def test_language_context_only_in_provenance(self) -> None:
        from domain.contracts.feature.feature_identity import FeatureIdentity
        lang_candidate = make_candidate(FeatureType.LANGUAGE_CAPABILITY)
        from domain.contracts.feature.feature_candidate import FeatureCandidate
        lang_candidate_with_ctx = FeatureCandidate(
            feature_identity=FeatureIdentity.for_type(FeatureType.LANGUAGE_CAPABILITY),
            candidate_value="HIGH",
            candidate_confidence=0.85,
            source_observation_ids=("obs-1",),
            computed_at_question_index=2,
            updater_id="stub_updater",
            language_context="python",
        )
        updater = StubUpdater(
            candidates_to_produce=[lang_candidate_with_ctx],
            feature_identity_set=frozenset({"language_capability_feature"}),
        )
        engine = FeatureEngine([updater], PassthroughComposer())
        result = engine.run(make_context())
        pf = result.features[0]
        # Language context is in provenance, not in feature_identity
        assert pf.provenance.language_context == "python"
        assert "python" not in pf.feature_identity.feature_type_id


class TestMultipleCyclesAccumulation:
    def test_multiple_cycles_all_succeed(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        for i in range(5):
            result = engine.run(make_context(question_index=i))
            assert result.is_successful is True

    def test_each_cycle_independent_for_base_engine(self) -> None:
        """Base FeatureEngine is stateless between calls."""
        c1 = make_candidate(FeatureType.REASONING, "HIGH")
        c2 = make_candidate(FeatureType.REASONING, "LOW")
        updater = StubUpdater(candidates_to_produce=[c1])
        engine = FeatureEngine([updater], PassthroughComposer())

        result1 = engine.run(make_context(question_index=0))

        updater._candidates = [c2]  # Change what updater produces
        result2 = engine.run(make_context(question_index=1))

        assert result1.features[0].value == "HIGH"
        assert result2.features[0].value == "LOW"

    def test_cycle_question_index_tracked_per_result(self) -> None:
        updater = StubUpdater(candidates_to_produce=[make_candidate()])
        engine = FeatureEngine([updater], PassthroughComposer())
        for i in range(3):
            result = engine.run(make_context(question_index=i))
            assert result.current_question_index == i
