# domain/observation/runtime/observation_ordering.py
# Ordering policies for deterministic Observation sequencing.

from __future__ import annotations

from enum import Enum
from typing import Callable

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_query import ObservationSortField, ObservationSortOrder


class ObservationOrderingPolicy(str, Enum):
    """Named ordering policies for runtime use.

    CHRONOLOGICAL       — question_index ASC (canonical session ordering).
    REVERSE_CHRONOLOGICAL — question_index DESC (most-recent-first).
    CONFIDENCE_DESC     — highest confidence first.
    CONFIDENCE_ASC      — lowest confidence first.
    WEIGHT_DESC         — highest decay weight first (most-relevant first).
    WEIGHT_ASC          — lowest decay weight first.
    OBSERVED_AT_ASC     — wall-clock timestamp ascending.
    OBSERVED_AT_DESC    — wall-clock timestamp descending.
    TYPE_THEN_CHRONOLOGICAL — group by type name, then question_index ASC.
    """

    CHRONOLOGICAL = "chronological"
    REVERSE_CHRONOLOGICAL = "reverse_chronological"
    CONFIDENCE_DESC = "confidence_desc"
    CONFIDENCE_ASC = "confidence_asc"
    WEIGHT_DESC = "weight_desc"
    WEIGHT_ASC = "weight_asc"
    OBSERVED_AT_ASC = "observed_at_asc"
    OBSERVED_AT_DESC = "observed_at_desc"
    TYPE_THEN_CHRONOLOGICAL = "type_then_chronological"


_POLICY_KEYS: dict[ObservationOrderingPolicy, tuple[Callable[[Observation], object], bool]] = {
    ObservationOrderingPolicy.CHRONOLOGICAL: (
        lambda o: o.metadata.question_index, False
    ),
    ObservationOrderingPolicy.REVERSE_CHRONOLOGICAL: (
        lambda o: o.metadata.question_index, True
    ),
    ObservationOrderingPolicy.CONFIDENCE_DESC: (
        lambda o: o.confidence, True
    ),
    ObservationOrderingPolicy.CONFIDENCE_ASC: (
        lambda o: o.confidence, False
    ),
    ObservationOrderingPolicy.WEIGHT_DESC: (
        lambda o: o.weight, True
    ),
    ObservationOrderingPolicy.WEIGHT_ASC: (
        lambda o: o.weight, False
    ),
    ObservationOrderingPolicy.OBSERVED_AT_ASC: (
        lambda o: o.metadata.observed_at, False
    ),
    ObservationOrderingPolicy.OBSERVED_AT_DESC: (
        lambda o: o.metadata.observed_at, True
    ),
    ObservationOrderingPolicy.TYPE_THEN_CHRONOLOGICAL: (
        lambda o: (o.observation_type.value, o.metadata.question_index), False
    ),
}


class ObservationOrdering:
    """Pure ordering utilities for Observation sequences.

    All methods are stateless and return new tuples without mutating input.
    """

    @staticmethod
    def apply(
        observations: tuple[Observation, ...] | list[Observation],
        policy: ObservationOrderingPolicy,
    ) -> tuple[Observation, ...]:
        """Return a new tuple sorted by the given policy."""
        key_fn, reverse = _POLICY_KEYS[policy]
        return tuple(sorted(observations, key=key_fn, reverse=reverse))  # type: ignore[arg-type]

    @staticmethod
    def from_query_fields(
        observations: tuple[Observation, ...] | list[Observation],
        sort_by: ObservationSortField,
        sort_order: ObservationSortOrder,
    ) -> tuple[Observation, ...]:
        """Apply sort derived from ObservationQuery sort_by / sort_order fields."""
        field_map: dict[ObservationSortField, Callable[[Observation], object]] = {
            ObservationSortField.QUESTION_INDEX: lambda o: o.metadata.question_index,
            ObservationSortField.OBSERVED_AT: lambda o: o.metadata.observed_at,
            ObservationSortField.CONFIDENCE: lambda o: o.confidence,
            ObservationSortField.WEIGHT: lambda o: o.weight,
        }
        reverse = sort_order == ObservationSortOrder.DESC
        return tuple(sorted(observations, key=field_map[sort_by], reverse=reverse))  # type: ignore[arg-type]

    @staticmethod
    def is_chronological(observations: tuple[Observation, ...]) -> bool:
        """Return True iff observations are sorted by question_index ASC."""
        return all(
            observations[i].metadata.question_index <= observations[i + 1].metadata.question_index
            for i in range(len(observations) - 1)
        )
