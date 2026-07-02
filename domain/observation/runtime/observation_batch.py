# domain/observation/runtime/observation_batch.py
# Immutable ordered collection of Observations produced in a single extraction cycle.

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType


class ObservationBatch(BaseModel):
    """Immutable collection of Observations from a single extraction pass.

    Invariants:
    - observations is ordered by question_index ASC (stable, deterministic).
    - question_index is uniform across all entries (same extraction turn).
    - session_id is uniform; all observations belong to the same session.
    - No mutation after construction (frozen=True).
    """

    session_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)
    observations: tuple[Observation, ...] = Field(default_factory=tuple)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_list(
        cls,
        session_id: str,
        question_index: int,
        observations: list[Observation],
    ) -> "ObservationBatch":
        """Build a batch from a mutable list, asserting session/index invariants."""
        for obs in observations:
            if obs.metadata.session_id != session_id:
                raise ValueError(
                    f"Observation {obs.id.value} belongs to session "
                    f"'{obs.metadata.session_id}', expected '{session_id}'"
                )
            if obs.metadata.question_index != question_index:
                raise ValueError(
                    f"Observation {obs.id.value} has question_index "
                    f"{obs.metadata.question_index}, expected {question_index}"
                )
        return cls(
            session_id=session_id,
            question_index=question_index,
            observations=tuple(observations),
        )

    @property
    def size(self) -> int:
        return len(self.observations)

    @property
    def is_empty(self) -> bool:
        return len(self.observations) == 0

    def by_type(self, observation_type: ObservationType) -> tuple[Observation, ...]:
        return tuple(o for o in self.observations if o.observation_type == observation_type)

    def active(self) -> tuple[Observation, ...]:
        return tuple(o for o in self.observations if o.status == ObservationStatus.ACTIVE)

    def types(self) -> frozenset[ObservationType]:
        return frozenset(o.observation_type for o in self.observations)
