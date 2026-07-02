# tests/domain/contracts/observation/test_observation_store_contract.py
# Validates ObservationStore ABC contract via an in-memory implementation.

from __future__ import annotations

from collections import defaultdict

import pytest
from pydantic import ValidationError

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_metadata import ObservationMetadata
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_query import ObservationQuery, ObservationSortField, ObservationSortOrder
from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.observation.observation_type import ObservationType


# ---------------------------------------------------------------------------
# Minimal in-memory implementation for contract testing
# ---------------------------------------------------------------------------

class InMemoryObservationStore(ObservationStore):
    """Minimal reference implementation for contract-level tests."""

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._store: dict[str, Observation] = {}

    def session_id(self) -> str:
        return self._session_id

    def count(self) -> int:
        return len(self._store)

    def append(self, observation: Observation) -> None:
        key = (
            observation.observation_type,
            observation.metadata.origin,
            observation.metadata.question_index,
            observation.metadata.session_id,
        )
        # Supersede existing ACTIVE entry for same key
        for oid, existing in list(self._store.items()):
            existing_key = (
                existing.observation_type,
                existing.metadata.origin,
                existing.metadata.question_index,
                existing.metadata.session_id,
            )
            if existing_key == key and existing.status == ObservationStatus.ACTIVE:
                self._store[oid] = existing.with_status(ObservationStatus.SUPERSEDED)
        self._store[observation.id.value] = observation

    def get(self, observation_id: ObservationId) -> Observation | None:
        return self._store.get(observation_id.value)

    def query(self, observation_query: ObservationQuery) -> list[Observation]:
        results = list(self._store.values())

        f = observation_query.filter
        if f.observation_types is not None:
            results = [o for o in results if o.observation_type in f.observation_types]
        if f.statuses is not None:
            results = [o for o in results if o.status in f.statuses]
        if f.origins is not None:
            results = [o for o in results if o.metadata.origin in f.origins]
        if f.session_id is not None:
            results = [o for o in results if o.metadata.session_id == f.session_id]
        if f.question_index_min is not None:
            results = [o for o in results if o.metadata.question_index >= f.question_index_min]
        if f.question_index_max is not None:
            results = [o for o in results if o.metadata.question_index <= f.question_index_max]
        if f.confidence_min is not None:
            results = [o for o in results if o.confidence >= f.confidence_min]
        if f.confidence_max is not None:
            results = [o for o in results if o.confidence <= f.confidence_max]

        reverse = observation_query.sort_order == ObservationSortOrder.DESC
        key_fn = {
            ObservationSortField.QUESTION_INDEX: lambda o: o.metadata.question_index,
            ObservationSortField.OBSERVED_AT: lambda o: o.metadata.observed_at,
            ObservationSortField.CONFIDENCE: lambda o: o.confidence,
            ObservationSortField.WEIGHT: lambda o: o.weight,
        }[observation_query.sort_by]
        results.sort(key=key_fn, reverse=reverse)

        start = observation_query.offset
        end = start + observation_query.limit
        return results[start:end]

    def snapshot(self) -> ObservationSnapshot:
        return ObservationSnapshot.from_observations(
            self._session_id, list(self._store.values())
        )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def store() -> InMemoryObservationStore:
    return InMemoryObservationStore("test-session")


def _obs(
    question_index: int = 0,
    observation_type: ObservationType = ObservationType.TECHNICAL_CORRECTNESS,
    confidence: float = 0.8,
    origin: ObservationOrigin = ObservationOrigin.EVALUATION,
    session_id: str = "test-session",
) -> Observation:
    meta = ObservationMetadata(
        question_index=question_index,
        session_id=session_id,
        origin=origin,
        source_ref="src",
    )
    return Observation(
        observation_type=observation_type,
        metadata=meta,
        description="generated observation",
        confidence=confidence,
    )


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------

class TestObservationStoreABC:
    def test_cannot_instantiate_abstract(self):
        with pytest.raises(TypeError):
            ObservationStore()  # type: ignore[abstract]


class TestObservationStoreAppend:
    def test_append_increases_count(self, store):
        store.append(_obs(0))
        assert store.count() == 1

    def test_append_multiple_increases_count(self, store):
        for i in range(5):
            store.append(_obs(i))
        assert store.count() == 5

    def test_appended_observation_retrievable_by_id(self, store):
        obs = _obs(0)
        store.append(obs)
        assert store.get(obs.id) == obs

    def test_get_nonexistent_returns_none(self, store):
        assert store.get(ObservationId.generate()) is None


class TestObservationStoreDeduplication:
    def test_duplicate_key_supersedes_existing(self, store):
        obs1 = _obs(0)
        obs2 = _obs(0)  # same type + origin + question_index + session
        store.append(obs1)
        store.append(obs2)
        assert store.count() == 2
        superseded = store.get(obs1.id)
        assert superseded.status == ObservationStatus.SUPERSEDED

    def test_duplicate_new_entry_is_active(self, store):
        obs1 = _obs(0)
        obs2 = _obs(0)
        store.append(obs1)
        store.append(obs2)
        active = store.get(obs2.id)
        assert active.status == ObservationStatus.ACTIVE

    def test_different_question_index_no_supersede(self, store):
        store.append(_obs(0))
        store.append(_obs(1))
        # both should remain ACTIVE
        q = ObservationQuery(filter=ObservationFilter(statuses=frozenset({ObservationStatus.ACTIVE})))
        results = store.query(q)
        assert len(results) == 2


class TestObservationStoreQuery:
    def test_empty_filter_returns_all(self, store):
        for i in range(3):
            store.append(_obs(i))
        results = store.query(ObservationQuery())
        assert len(results) == 3

    def test_filter_by_observation_type(self, store):
        store.append(_obs(0, ObservationType.TECHNICAL_CORRECTNESS))
        store.append(_obs(1, ObservationType.LEADERSHIP_STRONG))
        f = ObservationFilter(observation_types=frozenset({ObservationType.LEADERSHIP_STRONG}))
        results = store.query(ObservationQuery(filter=f))
        assert len(results) == 1
        assert results[0].observation_type == ObservationType.LEADERSHIP_STRONG

    def test_filter_by_confidence_min(self, store):
        store.append(_obs(0, confidence=0.3))
        store.append(_obs(1, confidence=0.9))
        f = ObservationFilter(confidence_min=0.8)
        results = store.query(ObservationQuery(filter=f))
        assert len(results) == 1
        assert results[0].confidence == pytest.approx(0.9)

    def test_sort_by_confidence_desc(self, store):
        store.append(_obs(0, confidence=0.3))
        store.append(_obs(1, confidence=0.9))
        store.append(_obs(2, confidence=0.6))
        q = ObservationQuery(sort_by=ObservationSortField.CONFIDENCE, sort_order=ObservationSortOrder.DESC)
        results = store.query(q)
        assert results[0].confidence == pytest.approx(0.9)
        assert results[-1].confidence == pytest.approx(0.3)

    def test_limit_applied(self, store):
        for i in range(10):
            store.append(_obs(i))
        results = store.query(ObservationQuery(limit=3))
        assert len(results) == 3

    def test_offset_applied(self, store):
        for i in range(5):
            store.append(_obs(i))
        q = ObservationQuery(
            sort_by=ObservationSortField.QUESTION_INDEX,
            sort_order=ObservationSortOrder.ASC,
            offset=2,
            limit=100,
        )
        results = store.query(q)
        assert len(results) == 3
        assert results[0].metadata.question_index == 2


class TestObservationStoreSnapshot:
    def test_snapshot_empty_store(self, store):
        snap = store.snapshot()
        assert snap.total_count == 0
        assert snap.session_id == "test-session"

    def test_snapshot_correct_counts(self, store):
        store.append(_obs(0))
        store.append(_obs(1))
        snap = store.snapshot()
        assert snap.total_count == 2
        assert snap.active_count == 2

    def test_snapshot_ordered_by_question_index(self, store):
        for i in [4, 2, 0, 3, 1]:
            store.append(_obs(i))
        snap = store.snapshot()
        indices = [o.metadata.question_index for o in snap.observations]
        assert indices == sorted(indices)

    def test_snapshot_is_immutable(self, store):
        snap = store.snapshot()
        with pytest.raises((TypeError, ValidationError)):
            snap.total_count = 99  # type: ignore[misc]
