# domain/contracts/observation/observation_store.py
# ADR-016: ObservationStore — Aggregate Root interface
# ADR-017: Lifecycle, append-only, deduplication, temporal ordering

from abc import ABC, abstractmethod

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_query import ObservationQuery
from domain.contracts.observation.observation_snapshot import ObservationSnapshot


class ObservationStore(ABC):
    """Append-only Aggregate Root for Observations (ADR-016, ADR-017).

    Boundary contract:
    - Sole writer: ObservationExtractor.
    - Readers: FeatureEngine, CalibrationProfile, ReplayUpdater.
    - No external component may mutate stored Observations directly.
    - Status transitions (ACTIVE → DECAYED → EXPIRED, ACTIVE → SUPERSEDED)
      are the responsibility of the store implementation, not callers.

    All implementations MUST be:
    - Append-only: append() is the only write operation.
    - Deterministic on deduplication: same (type, origin, question_index,
      session_id) triple supersedes the previous entry.
    - Thread-safe within a session scope.
    """

    @abstractmethod
    def append(self, observation: Observation) -> None:
        """Append an Observation to the store.

        Deduplication rule (ADR-017 Section D):
        If an observation with the same (observation_type, origin,
        question_index, session_id) already exists with status ACTIVE, the
        existing entry is transitioned to SUPERSEDED and the new one becomes
        ACTIVE.

        Raises:
            ValueError: if observation violates invariants (e.g. wrong session).
        """

    @abstractmethod
    def get(self, observation_id: ObservationId) -> Observation | None:
        """Return the Observation with the given id, or None if not found."""

    @abstractmethod
    def query(self, observation_query: ObservationQuery) -> list[Observation]:
        """Return Observations matching the query, ordered and paginated.

        Results respect the sort_by, sort_order, limit, and offset fields of
        the query. Filter predicates are applied with AND semantics.
        """

    @abstractmethod
    def snapshot(self) -> ObservationSnapshot:
        """Return an immutable point-in-time snapshot of the entire store.

        Observations are ordered by question_index ASC.
        Consumed by FeatureEngine and ReplayUpdater.
        """

    @abstractmethod
    def count(self) -> int:
        """Return the total number of stored Observations (all statuses)."""

    @abstractmethod
    def session_id(self) -> str:
        """Return the session identifier this store is scoped to."""
