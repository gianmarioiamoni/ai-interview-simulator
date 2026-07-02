# tests/domain/observation/runtime/test_runtime_integration.py
# Integration tests: all runtime objects working together via a shared store.

from __future__ import annotations

import pytest

from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_batch import ObservationBatch
from domain.observation.runtime.observation_collection import ObservationCollection
from domain.observation.runtime.observation_cursor import ObservationCursor
from domain.observation.runtime.observation_delta import ObservationDelta
from domain.observation.runtime.observation_ordering import ObservationOrdering, ObservationOrderingPolicy
from domain.observation.runtime.observation_statistics import ObservationStatistics
from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
from domain.observation.runtime.observation_store_snapshot_builder import ObservationStoreSnapshotBuilder
from tests.domain.observation.runtime.test_observation_store_query_engine import _Store
from tests.domain.observation.runtime.conftest import make_obs, SESSION


@pytest.fixture()
def populated_store() -> _Store:
    store = _Store()
    for i in range(5):
        store.append(make_obs(i, ObservationType.TECHNICAL_CORRECTNESS, confidence=0.5 + 0.1 * i))
    store.append(make_obs(5, ObservationType.KNOWLEDGE_GAP, confidence=0.4))
    return store


class TestRuntimePipeline:
    def test_batch_to_cursor_to_statistics(self):
        obs = [make_obs(0, confidence=0.7), make_obs(0, confidence=0.8)]
        batch = ObservationBatch.from_list(SESSION, 0, obs)
        cursor = ObservationCursor(batch.observations)
        collected: list = []
        while not cursor.exhausted:
            o = cursor.next()
            if o is not None:
                collected.append(o)
        stats = ObservationStatistics.from_observations(collected)
        assert stats.total == 2
        assert stats.mean_confidence == pytest.approx(0.75)

    def test_query_engine_collection_delta(self, populated_store: _Store):
        engine = ObservationStoreQueryEngine(populated_store)
        col_before = engine.all()

        # append new observation and compute delta
        new_obs = make_obs(6, ObservationType.REASONING_IMPROVING, confidence=0.9)
        populated_store.append(new_obs)
        col_after = engine.all()

        delta = ObservationDelta.compute(list(col_before.all), list(col_after.all))
        assert len(delta.added) >= 1
        added_ids = {o.id.value for o in delta.added}
        assert new_obs.id.value in added_ids

    def test_snapshot_builder_ordering_invariant(self, populated_store: _Store):
        builder = ObservationStoreSnapshotBuilder(populated_store)
        snap = builder.full()
        assert ObservationOrdering.is_chronological(snap.observations)

    def test_collection_filter_statistics_consistent(self, populated_store: _Store):
        engine = ObservationStoreQueryEngine(populated_store)
        col = engine.by_type(ObservationType.TECHNICAL_CORRECTNESS)
        stats = ObservationStatistics.from_observations(list(col.all))
        assert stats.distinct_types == 1

    def test_snapshot_active_only_matches_engine_active(self, populated_store: _Store):
        engine = ObservationStoreQueryEngine(populated_store)
        builder = ObservationStoreSnapshotBuilder(populated_store)

        engine_active_count = engine.count_active()
        snap_active = builder.active_only()
        assert snap_active.total_count == engine_active_count
