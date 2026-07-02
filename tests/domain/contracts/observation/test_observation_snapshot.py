# tests/domain/contracts/observation/test_observation_snapshot.py

import pytest
from pydantic import ValidationError

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType


def _obs(question_index: int = 0, status: ObservationStatus = ObservationStatus.ACTIVE) -> Observation:
    meta = ObservationMetadata(
        question_index=question_index,
        session_id="sess-001",
        origin=ObservationOrigin.EVALUATION,
        source_ref="ref",
    )
    obs = Observation(
        observation_type=ObservationType.TECHNICAL_CORRECTNESS,
        metadata=meta,
        description="desc",
        confidence=0.8,
    )
    if status != ObservationStatus.ACTIVE:
        obs = obs.with_status(status)
    return obs


class TestObservationSnapshotDefaults:
    def test_empty_snapshot_constructable(self):
        snap = ObservationSnapshot(session_id="s")
        assert snap.total_count == 0
        assert snap.observations == ()

    def test_schema_version_default(self):
        snap = ObservationSnapshot(session_id="s")
        assert snap.schema_version == "1.0"

    def test_snapshotted_at_is_set(self):
        snap = ObservationSnapshot(session_id="s")
        assert snap.snapshotted_at is not None


class TestObservationSnapshotImmutability:
    def test_frozen(self):
        snap = ObservationSnapshot(session_id="s")
        with pytest.raises(ValidationError):
            snap.total_count = 5

    def test_extra_fields_forbidden(self):
        with pytest.raises(ValidationError):
            ObservationSnapshot(session_id="s", extra="x")  # type: ignore[call-arg]

    def test_observations_is_tuple(self):
        snap = ObservationSnapshot.from_observations("s", [_obs()])
        assert isinstance(snap.observations, tuple)


class TestObservationSnapshotFromObservations:
    def test_empty_list(self):
        snap = ObservationSnapshot.from_observations("s", [])
        assert snap.total_count == 0
        assert snap.active_count == 0

    def test_single_active_observation(self):
        snap = ObservationSnapshot.from_observations("s", [_obs(0, ObservationStatus.ACTIVE)])
        assert snap.total_count == 1
        assert snap.active_count == 1
        assert snap.decayed_count == 0
        assert snap.expired_count == 0
        assert snap.superseded_count == 0

    def test_mixed_statuses_counted(self):
        observations = [
            _obs(0, ObservationStatus.ACTIVE),
            _obs(1, ObservationStatus.DECAYED),
            _obs(2, ObservationStatus.EXPIRED),
            _obs(3, ObservationStatus.SUPERSEDED),
            _obs(4, ObservationStatus.ACTIVE),
        ]
        snap = ObservationSnapshot.from_observations("s", observations)
        assert snap.total_count == 5
        assert snap.active_count == 2
        assert snap.decayed_count == 1
        assert snap.expired_count == 1
        assert snap.superseded_count == 1

    def test_ordered_by_question_index_asc(self):
        observations = [_obs(3), _obs(1), _obs(2), _obs(0)]
        snap = ObservationSnapshot.from_observations("s", observations)
        indices = [o.metadata.question_index for o in snap.observations]
        assert indices == sorted(indices)

    def test_session_id_stored(self):
        snap = ObservationSnapshot.from_observations("my-session", [])
        assert snap.session_id == "my-session"

    def test_total_count_equals_len(self):
        observations = [_obs(i) for i in range(10)]
        snap = ObservationSnapshot.from_observations("s", observations)
        assert snap.total_count == len(snap.observations)


class TestObservationSnapshotValidation:
    def test_empty_session_id_raises(self):
        with pytest.raises(ValidationError):
            ObservationSnapshot(session_id="")

    def test_negative_count_raises(self):
        with pytest.raises(ValidationError):
            ObservationSnapshot(session_id="s", total_count=-1)
