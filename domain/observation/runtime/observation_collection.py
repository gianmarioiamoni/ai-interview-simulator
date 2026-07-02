# domain/observation/runtime/observation_collection.py
# Filtered, grouped, and aggregated view over a set of Observations.

from __future__ import annotations

from collections import defaultdict
from typing import Callable

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_filter import ObservationFilter
from domain.contracts.observation.observation_origin import ObservationOrigin
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.observation.runtime.observation_ordering import (
    ObservationOrdering,
    ObservationOrderingPolicy,
)


def _matches(obs: Observation, f: ObservationFilter) -> bool:
    """Return True iff obs satisfies all predicates in filter f (AND semantics)."""
    if f.observation_types is not None and obs.observation_type not in f.observation_types:
        return False
    if f.statuses is not None and obs.status not in f.statuses:
        return False
    if f.origins is not None and obs.metadata.origin not in f.origins:
        return False
    if f.session_id is not None and obs.metadata.session_id != f.session_id:
        return False
    if f.question_index_min is not None and obs.metadata.question_index < f.question_index_min:
        return False
    if f.question_index_max is not None and obs.metadata.question_index > f.question_index_max:
        return False
    if f.observed_after is not None and obs.metadata.observed_at <= f.observed_after:
        return False
    if f.observed_before is not None and obs.metadata.observed_at >= f.observed_before:
        return False
    if f.confidence_min is not None and obs.confidence < f.confidence_min:
        return False
    if f.confidence_max is not None and obs.confidence > f.confidence_max:
        return False
    if f.weight_min is not None and obs.weight < f.weight_min:
        return False
    if f.weight_max is not None and obs.weight > f.weight_max:
        return False
    if f.tags_any is not None and not (obs.tags & f.tags_any):
        return False
    if f.tags_all is not None and not f.tags_all.issubset(obs.tags):
        return False
    return True


class ObservationCollection:
    """Runtime view: filter, group, and aggregate an Observation sequence.

    Constructed from an immutable tuple; all operations return new collections
    or plain Python structures without mutating state.
    """

    def __init__(self, observations: tuple[Observation, ...]) -> None:
        self._observations: tuple[Observation, ...] = observations

    @classmethod
    def from_list(cls, observations: list[Observation]) -> "ObservationCollection":
        return cls(tuple(observations))

    @property
    def all(self) -> tuple[Observation, ...]:
        return self._observations

    @property
    def size(self) -> int:
        return len(self._observations)

    # ------------------------------------------------------------------
    # Filtering
    # ------------------------------------------------------------------

    def filter(self, observation_filter: ObservationFilter) -> "ObservationCollection":
        """Return a new collection containing only matching observations."""
        return ObservationCollection(
            tuple(o for o in self._observations if _matches(o, observation_filter))
        )

    def where(self, predicate: Callable[[Observation], bool]) -> "ObservationCollection":
        """Return a new collection filtered by arbitrary predicate."""
        return ObservationCollection(tuple(o for o in self._observations if predicate(o)))

    def active(self) -> "ObservationCollection":
        return self.where(lambda o: o.status == ObservationStatus.ACTIVE)

    def by_type(self, observation_type: ObservationType) -> "ObservationCollection":
        return self.where(lambda o: o.observation_type == observation_type)

    def by_origin(self, origin: ObservationOrigin) -> "ObservationCollection":
        return self.where(lambda o: o.metadata.origin == origin)

    def by_question_index(self, question_index: int) -> "ObservationCollection":
        return self.where(lambda o: o.metadata.question_index == question_index)

    def with_min_confidence(self, min_confidence: float) -> "ObservationCollection":
        return self.where(lambda o: o.confidence >= min_confidence)

    # ------------------------------------------------------------------
    # Grouping
    # ------------------------------------------------------------------

    def group_by_type(self) -> dict[ObservationType, tuple[Observation, ...]]:
        groups: dict[ObservationType, list[Observation]] = defaultdict(list)
        for obs in self._observations:
            groups[obs.observation_type].append(obs)
        return {k: tuple(v) for k, v in groups.items()}

    def group_by_question_index(self) -> dict[int, tuple[Observation, ...]]:
        groups: dict[int, list[Observation]] = defaultdict(list)
        for obs in self._observations:
            groups[obs.metadata.question_index].append(obs)
        return {k: tuple(v) for k, v in sorted(groups.items())}

    def group_by_status(self) -> dict[ObservationStatus, tuple[Observation, ...]]:
        groups: dict[ObservationStatus, list[Observation]] = defaultdict(list)
        for obs in self._observations:
            groups[obs.status].append(obs)
        return {k: tuple(v) for k, v in groups.items()}

    def group_by_origin(self) -> dict[ObservationOrigin, tuple[Observation, ...]]:
        groups: dict[ObservationOrigin, list[Observation]] = defaultdict(list)
        for obs in self._observations:
            groups[obs.metadata.origin].append(obs)
        return {k: tuple(v) for k, v in groups.items()}

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def average_confidence(self) -> float | None:
        """Return mean confidence, or None if collection is empty."""
        if not self._observations:
            return None
        return sum(o.confidence for o in self._observations) / len(self._observations)

    def average_weight(self) -> float | None:
        """Return mean decay weight, or None if collection is empty."""
        if not self._observations:
            return None
        return sum(o.weight for o in self._observations) / len(self._observations)

    def count_by_type(self) -> dict[ObservationType, int]:
        counts: dict[ObservationType, int] = defaultdict(int)
        for obs in self._observations:
            counts[obs.observation_type] += 1
        return dict(counts)

    def count_by_status(self) -> dict[ObservationStatus, int]:
        counts: dict[ObservationStatus, int] = defaultdict(int)
        for obs in self._observations:
            counts[obs.status] += 1
        return dict(counts)

    def distinct_types(self) -> frozenset[ObservationType]:
        return frozenset(o.observation_type for o in self._observations)

    def top_by_confidence(self, n: int) -> tuple[Observation, ...]:
        """Return the n highest-confidence observations."""
        return ObservationOrdering.apply(
            self._observations, ObservationOrderingPolicy.CONFIDENCE_DESC
        )[:n]

    def ordered(
        self, policy: ObservationOrderingPolicy = ObservationOrderingPolicy.CHRONOLOGICAL
    ) -> "ObservationCollection":
        return ObservationCollection(ObservationOrdering.apply(self._observations, policy))
