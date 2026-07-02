# tests/domain/observation/runtime/test_observation_store_snapshot_builder.py

from __future__ import annotations

import pytest

from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_store_snapshot_builder import ObservationStoreSnapshotBuilder
from tests.domain.observation.runtime.test_observation_store_query_engine import _Store
from tests.domain.observation.runtime.conftest import make_obs, SESSION


@pytest.fixture()
def store() -> _Store:
    return _Store()


@pytest.fixture()
def builder(store: _Store) -> ObservationStoreSnapshotBuilder:
    return ObservationStoreSnapshotBuilder(store)


class TestSnapshotBuilderFull:
    def test_full_empty_store(self, builder: ObservationStoreSnapshotBuilder):
        snap = builder.full()
        assert snap.total_count == 0
        assert snap.session_id == SESSION

    def test_full_returns_all(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        for i in range(4):
            store.append(make_obs(i))
        snap = builder.full()
        assert snap.total_count == 4

    def test_full_ordered_by_question_index(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        for i in [3, 1, 2, 0]:
            store.append(make_obs(i))
        snap = builder.full()
        indices = [o.metadata.question_index for o in snap.observations]
        assert indices == sorted(indices)

    def test_full_snapshot_is_immutable(self, builder: ObservationStoreSnapshotBuilder):
        snap = builder.full()
        with pytest.raises(Exception):
            snap.total_count = 99  # type: ignore[misc]


class TestSnapshotBuilderActiveOnly:
    def test_active_only_excludes_superseded(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        store.append(make_obs(0))
        store.append(make_obs(0))  # supersedes first
        snap = builder.active_only()
        assert all(o.status == ObservationStatus.ACTIVE for o in snap.observations)
        assert snap.active_count == snap.total_count


class TestSnapshotBuilderFiltered:
    def test_filtered_by_type(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        store.append(make_obs(0, ObservationType.KNOWLEDGE_GAP))
        store.append(make_obs(1, ObservationType.TECHNICAL_CORRECTNESS))
        f = ObservationFilter(observation_types=frozenset({ObservationType.KNOWLEDGE_GAP}))
        snap = builder.filtered(f)
        assert snap.total_count == 1
        assert snap.observations[0].observation_type == ObservationType.KNOWLEDGE_GAP


class TestSnapshotBuilderByType:
    def test_by_type_single(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        store.append(make_obs(0, ObservationType.REASONING_IMPROVING))
        store.append(make_obs(1, ObservationType.KNOWLEDGE_GAP))
        snap = builder.by_type(ObservationType.REASONING_IMPROVING)
        assert snap.total_count == 1

    def test_by_type_multiple(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        store.append(make_obs(0, ObservationType.REASONING_IMPROVING))
        store.append(make_obs(1, ObservationType.KNOWLEDGE_GAP))
        store.append(make_obs(2, ObservationType.TECHNICAL_CORRECTNESS))
        snap = builder.by_type(ObservationType.REASONING_IMPROVING, ObservationType.KNOWLEDGE_GAP)
        assert snap.total_count == 2


class TestSnapshotBuilderRange:
    def test_range_inclusive(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        for i in range(6):
            store.append(make_obs(i))
        snap = builder.range(1, 3)
        indices = [o.metadata.question_index for o in snap.observations]
        assert all(1 <= idx <= 3 for idx in indices)
        assert len(indices) == 3

    def test_range_invalid_raises(self, builder: ObservationStoreSnapshotBuilder):
        with pytest.raises(ValueError):
            builder.range(5, 2)

    def test_range_single_index(self, store: _Store, builder: ObservationStoreSnapshotBuilder):
        store.append(make_obs(3))
        snap = builder.range(3, 3)
        assert snap.total_count == 1
