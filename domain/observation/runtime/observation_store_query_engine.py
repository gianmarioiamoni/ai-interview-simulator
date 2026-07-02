# domain/observation/runtime/observation_store_query_engine.py
# Runtime query engine wrapping ObservationStore with collection-level operations.

from __future__ import annotations

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_query import (
    ObservationQuery,
    ObservationSortField,
    ObservationSortOrder,
)
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_collection import ObservationCollection
from domain.observation.runtime.observation_statistics import ObservationStatistics


class ObservationStoreQueryEngine:
    """Runtime facade over ObservationStore for rich query and collection operations.

    Wraps the raw ObservationStore ABC and exposes:
    - Structured query → ObservationCollection (with filtering / grouping / aggregation)
    - Convenience accessors (active_only, by_type, by_question_index, etc.)
    - Inline statistics without building a full snapshot.

    The engine is read-only; it never calls store.append().
    """

    def __init__(self, store: ObservationStore) -> None:
        self._store = store

    # ------------------------------------------------------------------
    # Full collection retrieval
    # ------------------------------------------------------------------

    def all(self, limit: int = 1000) -> ObservationCollection:
        """Return all observations (up to limit) as an ObservationCollection."""
        results = self._store.query(ObservationQuery(limit=limit))
        return ObservationCollection.from_list(results)

    # ------------------------------------------------------------------
    # Structured queries
    # ------------------------------------------------------------------

    def query(self, observation_query: ObservationQuery) -> ObservationCollection:
        """Execute a structured query and wrap the result in ObservationCollection."""
        return ObservationCollection.from_list(
            self._store.query(observation_query)
        )

    def query_filter(
        self,
        observation_filter: ObservationFilter,
        sort_by: ObservationSortField = ObservationSortField.QUESTION_INDEX,
        sort_order: ObservationSortOrder = ObservationSortOrder.ASC,
        limit: int = 1000,
        offset: int = 0,
    ) -> ObservationCollection:
        """Convenience method: build a query from filter + sort params."""
        q = ObservationQuery(
            filter=observation_filter,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )
        return self.query(q)

    # ------------------------------------------------------------------
    # Convenience accessors
    # ------------------------------------------------------------------

    def active_only(self) -> ObservationCollection:
        f = ObservationFilter(statuses=frozenset({ObservationStatus.ACTIVE}))
        return self.query_filter(f)

    def by_type(self, observation_type: ObservationType) -> ObservationCollection:
        f = ObservationFilter(observation_types=frozenset({observation_type}))
        return self.query_filter(f)

    def by_question_index(self, question_index: int) -> ObservationCollection:
        f = ObservationFilter(
            question_index_min=question_index,
            question_index_max=question_index,
        )
        return self.query_filter(f)

    def active_by_type(self, observation_type: ObservationType) -> ObservationCollection:
        f = ObservationFilter(
            observation_types=frozenset({observation_type}),
            statuses=frozenset({ObservationStatus.ACTIVE}),
        )
        return self.query_filter(f)

    def with_min_confidence(self, min_confidence: float) -> ObservationCollection:
        f = ObservationFilter(confidence_min=min_confidence)
        return self.query_filter(f)

    # ------------------------------------------------------------------
    # Statistics
    # ------------------------------------------------------------------

    def statistics(self, observation_filter: ObservationFilter | None = None) -> ObservationStatistics:
        """Compute runtime statistics, optionally scoped to a filter."""
        if observation_filter is not None:
            col = self.query_filter(observation_filter)
        else:
            col = self.all()
        return ObservationStatistics.from_observations(list(col.all))

    # ------------------------------------------------------------------
    # Counts
    # ------------------------------------------------------------------

    def count(self) -> int:
        return self._store.count()

    def count_active(self) -> int:
        f = ObservationFilter(statuses=frozenset({ObservationStatus.ACTIVE}))
        return len(self.query_filter(f).all)

    def session_id(self) -> str:
        return self._store.session_id()
