# tests/domain/observation/runtime/test_observation_store_query_engine.py

from __future__ import annotations

from collections import defaultdict

import pytest

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_query import ObservationQuery, ObservationSortField, ObservationSortOrder
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_store_query_engine import ObservationStoreQueryEngine
from tests.domain.observation.runtime.conftest import make_obs, SESSION


# ---------------------------------------------------------------------------
# Minimal in-memory store (test double)
# ---------------------------------------------------------------------------

class _Store(ObservationStore):
    def __init__(self) -> None:
        self._data: dict[str, Observation] = {}

    def session_id(self) -> str:
        return SESSION

    def count(self) -> int:
        return len(self._data)

    def append(self, observation: Observation) -> None:
        key = (
            observation.observation_type,
            observation.metadata.origin,
            observation.metadata.question_index,
            observation.metadata.session_id,
        )
        for oid, existing in list(self._data.items()):
            ek = (
                existing.observation_type,
                existing.metadata.origin,
                existing.metadata.question_index,
                existing.metadata.session_id,
            )
            if ek == key and existing.status == ObservationStatus.ACTIVE:
                self._data[oid] = existing.with_status(ObservationStatus.SUPERSEDED)
        self._data[observation.id.value] = observation

    def get(self, observation_id: ObservationId) -> Observation | None:
        return self._data.get(observation_id.value)

    def query(self, observation_query: ObservationQuery) -> list[Observation]:
        results = list(self._data.values())
        f = observation_query.filter
        if f.observation_types:
            results = [o for o in results if o.observation_type in f.observation_types]
        if f.statuses:
            results = [o for o in results if o.status in f.statuses]
        if f.confidence_min is not None:
            results = [o for o in results if o.confidence >= f.confidence_min]
        if f.question_index_min is not None:
            results = [o for o in results if o.metadata.question_index >= f.question_index_min]
        if f.question_index_max is not None:
            results = [o for o in results if o.metadata.question_index <= f.question_index_max]
        if f.tags_any is not None:
            results = [o for o in results if o.tags & f.tags_any]
        if f.tags_all is not None:
            results = [o for o in results if f.tags_all.issubset(o.tags)]
        reverse = observation_query.sort_order == ObservationSortOrder.DESC
        key_fn = {
            ObservationSortField.QUESTION_INDEX: lambda o: o.metadata.question_index,
            ObservationSortField.CONFIDENCE: lambda o: o.confidence,
            ObservationSortField.WEIGHT: lambda o: o.weight,
            ObservationSortField.OBSERVED_AT: lambda o: o.metadata.observed_at,
        }[observation_query.sort_by]
        results.sort(key=key_fn, reverse=reverse)
        return results[observation_query.offset: observation_query.offset + observation_query.limit]

    def snapshot(self) -> ObservationSnapshot:
        return ObservationSnapshot.from_observations(SESSION, list(self._data.values()))


@pytest.fixture()
def store() -> _Store:
    return _Store()


@pytest.fixture()
def engine(store: _Store) -> ObservationStoreQueryEngine:
    return ObservationStoreQueryEngine(store)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestQueryEngineAll:
    def test_all_empty(self, engine: ObservationStoreQueryEngine):
        assert engine.all().size == 0

    def test_all_returns_all(self, store: _Store, engine: ObservationStoreQueryEngine):
        for i in range(5):
            store.append(make_obs(i))
        assert engine.all().size == 5


class TestQueryEngineConvenience:
    def test_active_only(self, store: _Store, engine: ObservationStoreQueryEngine):
        store.append(make_obs(0))
        store.append(make_obs(0))  # supersedes obs at q0
        active = engine.active_only()
        assert all(o.status == ObservationStatus.ACTIVE for o in active.all)

    def test_by_type(self, store: _Store, engine: ObservationStoreQueryEngine):
        store.append(make_obs(0, ObservationType.KNOWLEDGE_GAP))
        store.append(make_obs(1, ObservationType.TECHNICAL_CORRECTNESS))
        result = engine.by_type(ObservationType.KNOWLEDGE_GAP)
        assert result.size == 1

    def test_by_question_index(self, store: _Store, engine: ObservationStoreQueryEngine):
        for i in range(4):
            store.append(make_obs(i))
        assert engine.by_question_index(2).size == 1

    def test_with_min_confidence(self, store: _Store, engine: ObservationStoreQueryEngine):
        store.append(make_obs(0, confidence=0.3))
        store.append(make_obs(1, confidence=0.9))
        assert engine.with_min_confidence(0.8).size == 1


class TestQueryEngineStatistics:
    def test_statistics_returns_correct_total(self, store: _Store, engine: ObservationStoreQueryEngine):
        for i in range(3):
            store.append(make_obs(i))
        stats = engine.statistics()
        assert stats.total == 3

    def test_statistics_with_filter(self, store: _Store, engine: ObservationStoreQueryEngine):
        store.append(make_obs(0, ObservationType.KNOWLEDGE_GAP, confidence=0.9))
        store.append(make_obs(1, ObservationType.TECHNICAL_CORRECTNESS, confidence=0.5))
        f = ObservationFilter(observation_types=frozenset({ObservationType.KNOWLEDGE_GAP}))
        stats = engine.statistics(f)
        assert stats.total == 1


class TestQueryEngineCounts:
    def test_count(self, store: _Store, engine: ObservationStoreQueryEngine):
        store.append(make_obs(0))
        assert engine.count() == 1

    def test_session_id(self, engine: ObservationStoreQueryEngine):
        assert engine.session_id() == SESSION
