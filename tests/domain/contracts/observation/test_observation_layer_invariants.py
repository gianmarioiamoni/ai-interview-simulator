# tests/domain/contracts/observation/test_observation_layer_invariants.py
# Architecture invariants: ADR-016, ADR-017, ADR-021, ADR-022

import inspect

import pytest

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_query import ObservationQuery
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.observation.observation_type import ObservationType


class TestImmutabilityInvariant:
    """All domain contracts must be frozen (ADR-016)."""

    def test_observation_is_frozen(self):
        assert Observation.model_config.get("frozen") is True

    def test_observation_id_is_frozen(self):
        assert ObservationId.model_config.get("frozen") is True

    def test_observation_metadata_is_frozen(self):
        assert ObservationMetadata.model_config.get("frozen") is True

    def test_observation_filter_is_frozen(self):
        assert ObservationFilter.model_config.get("frozen") is True

    def test_observation_query_is_frozen(self):
        assert ObservationQuery.model_config.get("frozen") is True

    def test_observation_snapshot_is_frozen(self):
        assert ObservationSnapshot.model_config.get("frozen") is True


class TestExtraForbiddenInvariant:
    """All domain contracts must have extra='forbid' (ADR-016)."""

    def test_observation_extra_forbid(self):
        assert Observation.model_config.get("extra") == "forbid"

    def test_observation_id_extra_forbid(self):
        assert ObservationId.model_config.get("extra") == "forbid"

    def test_observation_metadata_extra_forbid(self):
        assert ObservationMetadata.model_config.get("extra") == "forbid"

    def test_observation_filter_extra_forbid(self):
        assert ObservationFilter.model_config.get("extra") == "forbid"

    def test_observation_query_extra_forbid(self):
        assert ObservationQuery.model_config.get("extra") == "forbid"

    def test_observation_snapshot_extra_forbid(self):
        assert ObservationSnapshot.model_config.get("extra") == "forbid"


class TestSchemaVersionInvariant:
    """All versioned contracts carry schema_version (ADR-022)."""

    def _make_meta(self):
        return ObservationMetadata(
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.REPLAY,
        )

    def test_observation_has_schema_version(self):
        obs = Observation(
            observation_type=ObservationType.TECHNICAL_CORRECTNESS,
            metadata=self._make_meta(),
            description="test",
            confidence=0.5,
        )
        assert hasattr(obs, "schema_version")
        assert obs.schema_version == "1.0"

    def test_observation_id_has_schema_version(self):
        oid = ObservationId()
        assert oid.schema_version == "1.0"

    def test_observation_metadata_has_schema_version(self):
        meta = self._make_meta()
        assert meta.schema_version == "1.0"

    def test_observation_filter_has_schema_version(self):
        f = ObservationFilter()
        assert f.schema_version == "1.0"

    def test_observation_query_has_schema_version(self):
        q = ObservationQuery()
        assert q.schema_version == "1.0"

    def test_observation_snapshot_has_schema_version(self):
        snap = ObservationSnapshot(session_id="s")
        assert snap.schema_version == "1.0"


class TestObservationStoreIsAbstract:
    """ObservationStore must be an ABC with required abstract methods (ADR-016)."""

    def test_is_abstract(self):
        assert inspect.isabstract(ObservationStore)

    def test_abstract_methods_present(self):
        expected = {"append", "get", "query", "snapshot", "count", "session_id"}
        assert expected.issubset(ObservationStore.__abstractmethods__)

    def test_cannot_instantiate(self):
        with pytest.raises(TypeError):
            ObservationStore()  # type: ignore[abstract]


class TestObservationOriginBoundaryInvariant:
    """REPLAY and CALIBRATION origins must not require source_ref (ADR-016 A-2)."""

    def test_replay_no_source_ref(self):
        meta = ObservationMetadata(
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.REPLAY,
        )
        assert meta.source_ref is None

    def test_calibration_no_source_ref(self):
        meta = ObservationMetadata(
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.CALIBRATION,
        )
        assert meta.source_ref is None

    def test_evaluation_requires_source_ref(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            ObservationMetadata(
                question_index=0,
                session_id="s",
                origin=ObservationOrigin.EVALUATION,
                source_ref=None,
            )


class TestObservationTypeRegistryInvariant:
    """ObservationType must cover all ADR-066 behavioral types."""

    ADR066_TYPES = [
        ObservationType.LEADERSHIP_STRONG,
        ObservationType.LEADERSHIP_EMERGING,
        ObservationType.LEADERSHIP_ABSENT,
        ObservationType.COLLABORATION_STRONG,
        ObservationType.COLLABORATION_EFFECTIVE,
        ObservationType.COLLABORATION_DEFICIT,
        ObservationType.ADAPTABILITY_HIGH,
        ObservationType.ADAPTABILITY_MODERATE,
        ObservationType.ADAPTABILITY_LOW,
    ]

    def test_all_adr066_types_registered(self):
        for t in self.ADR066_TYPES:
            assert t in ObservationType

    def test_no_duplicate_values_in_registry(self):
        values = [t.value for t in ObservationType]
        assert len(values) == len(set(values))


class TestObservationStatusTransitionInvariant:
    """Status transitions must be representable via with_status (ADR-017)."""

    def _make_active_obs(self) -> Observation:
        meta = ObservationMetadata(
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.EVALUATION,
            source_ref="ref",
        )
        return Observation(
            observation_type=ObservationType.TECHNICAL_CORRECTNESS,
            metadata=meta,
            description="desc",
            confidence=0.8,
        )

    def test_active_to_decayed(self):
        obs = self._make_active_obs()
        decayed = obs.with_status(ObservationStatus.DECAYED)
        assert decayed.status == ObservationStatus.DECAYED

    def test_active_to_expired(self):
        obs = self._make_active_obs()
        expired = obs.with_status(ObservationStatus.EXPIRED)
        assert expired.status == ObservationStatus.EXPIRED

    def test_active_to_superseded(self):
        obs = self._make_active_obs()
        superseded = obs.with_status(ObservationStatus.SUPERSEDED)
        assert superseded.status == ObservationStatus.SUPERSEDED

    def test_transition_preserves_id(self):
        obs = self._make_active_obs()
        decayed = obs.with_status(ObservationStatus.DECAYED)
        assert decayed.id == obs.id

    def test_transition_preserves_type(self):
        obs = self._make_active_obs()
        decayed = obs.with_status(ObservationStatus.DECAYED)
        assert decayed.observation_type == obs.observation_type


class TestObservationDecayWeightInvariant:
    """Weight must always be in (0.0, 1.0] and updated via with_weight."""

    def _make_obs(self) -> Observation:
        meta = ObservationMetadata(
            question_index=0,
            session_id="s",
            origin=ObservationOrigin.EVALUATION,
            source_ref="ref",
        )
        return Observation(
            observation_type=ObservationType.TECHNICAL_CORRECTNESS,
            metadata=meta,
            description="desc",
            confidence=0.8,
        )

    def test_initial_weight_one(self):
        obs = self._make_obs()
        assert obs.weight == 1.0

    def test_weight_after_decay(self):
        obs = self._make_obs()
        decayed = obs.with_weight(0.5)
        assert decayed.weight == pytest.approx(0.5)

    def test_weight_cannot_be_zero(self):
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            self._make_obs().with_weight(0.0)

    def test_weight_chain_preserves_id(self):
        obs = self._make_obs()
        lighter = obs.with_weight(0.7)
        assert lighter.id == obs.id
