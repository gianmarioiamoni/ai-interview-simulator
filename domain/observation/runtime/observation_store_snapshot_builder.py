# domain/observation/runtime/observation_store_snapshot_builder.py
# Builds immutable ObservationSnapshot objects from a store or collection.

from __future__ import annotations

from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_query import (
    ObservationQuery,
    ObservationSortField,
    ObservationSortOrder,
)
from domain.contracts.observation.observation_snapshot import ObservationSnapshot
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.observation.observation_type import ObservationType


class ObservationStoreSnapshotBuilder:
    """Constructs immutable ObservationSnapshot objects from an ObservationStore.

    Supported snapshot variants:
    - full():         all observations, question_index ASC (equivalent to store.snapshot()).
    - active_only():  ACTIVE observations only.
    - filtered():     scoped to a caller-supplied ObservationFilter.
    - by_type():      scoped to one or more ObservationType values.
    - range():        scoped to a question_index window [min, max].

    The builder is stateless; each method call produces a fresh snapshot.
    The underlying store is never mutated.
    """

    def __init__(self, store: ObservationStore) -> None:
        self._store = store

    def full(self) -> ObservationSnapshot:
        """Full snapshot — delegates to store.snapshot() for canonical ordering."""
        return self._store.snapshot()

    def active_only(self) -> ObservationSnapshot:
        """Snapshot containing only ACTIVE observations."""
        f = ObservationFilter(statuses=frozenset({ObservationStatus.ACTIVE}))
        return self._build_from_filter(f)

    def filtered(self, observation_filter: ObservationFilter) -> ObservationSnapshot:
        """Snapshot scoped by an arbitrary ObservationFilter."""
        return self._build_from_filter(observation_filter)

    def by_type(self, *observation_types: ObservationType) -> ObservationSnapshot:
        """Snapshot containing only observations of the given type(s)."""
        f = ObservationFilter(observation_types=frozenset(observation_types))
        return self._build_from_filter(f)

    def range(self, question_index_min: int, question_index_max: int) -> ObservationSnapshot:
        """Snapshot scoped to a question_index window [min, max] (inclusive)."""
        if question_index_min > question_index_max:
            raise ValueError(
                f"question_index_min ({question_index_min}) must be "
                f"<= question_index_max ({question_index_max})"
            )
        f = ObservationFilter(
            question_index_min=question_index_min,
            question_index_max=question_index_max,
        )
        return self._build_from_filter(f)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_from_filter(self, observation_filter: ObservationFilter) -> ObservationSnapshot:
        q = ObservationQuery(
            filter=observation_filter,
            sort_by=ObservationSortField.QUESTION_INDEX,
            sort_order=ObservationSortOrder.ASC,
            limit=1000,
        )
        observations = self._store.query(q)
        return ObservationSnapshot.from_observations(
            session_id=self._store.session_id(),
            observations=observations,
        )
