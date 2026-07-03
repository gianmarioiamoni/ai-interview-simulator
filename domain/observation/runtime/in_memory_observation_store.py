# domain/observation/runtime/in_memory_observation_store.py
# Production ObservationStore implementation — session-scoped, append-only.
# ADR-016, ADR-017: InMemoryObservationStore is the V1.2 runtime store.
#
# Invariants:
# - Append-only: only ObservationExtractor may call append().
# - Deduplication: same (type, origin, question_index, session_id) supersedes
#   any prior ACTIVE observation of the same key (ADR-017).
# - snapshot() returns an immutable point-in-time view.
# - No LLM, no I/O, no shared mutable state across instances.

from __future__ import annotations

from typing import Any

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_query import ObservationQuery
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_store import ObservationStore


class InMemoryObservationStore(ObservationStore):
    """Session-scoped, in-memory ObservationStore (production implementation).

    Keyed by ObservationId.value.  Deduplication is applied on append():
    an existing ACTIVE observation with the same (type, origin, question_index,
    session_id) tuple is transitioned to SUPERSEDED before the new one is
    inserted (ADR-017 §4).

    Thread-safety: NOT thread-safe. Designed for single-session, single-thread
    use within a LangGraph node cycle.
    """

    def __init__(self, session_id: str) -> None:
        if not session_id or not session_id.strip():
            raise ValueError("session_id must be non-empty")
        self._session_id: str = session_id
        self._store: dict[str, Observation] = {}

    # ------------------------------------------------------------------
    # ObservationStore ABC
    # ------------------------------------------------------------------

    def session_id(self) -> str:
        return self._session_id

    def count(self) -> int:
        return len(self._store)

    def append(self, observation: Observation) -> None:
        """Append an Observation, superseding any active duplicate."""
        key = (
            observation.observation_type,
            observation.metadata.origin,
            observation.metadata.question_index,
            observation.metadata.session_id,
        )
        for oid, existing in list(self._store.items()):
            ek = (
                existing.observation_type,
                existing.metadata.origin,
                existing.metadata.question_index,
                existing.metadata.session_id,
            )
            if ek == key and existing.status == ObservationStatus.ACTIVE:
                self._store[oid] = existing.with_status(ObservationStatus.SUPERSEDED)
        self._store[observation.id.value] = observation

    def get(self, observation_id: Any) -> Observation | None:
        key = observation_id.value if isinstance(observation_id, ObservationId) else observation_id
        return self._store.get(key)

    def query(self, observation_query: ObservationQuery) -> list[Observation]:
        return list(self._store.values())

    def snapshot(self) -> ObservationSnapshot:
        return ObservationSnapshot.from_observations(
            self._session_id, list(self._store.values())
        )
