# domain/observation/runtime/observation_statistics.py
# Runtime statistics computed over an Observation population.

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_status import ObservationStatus
from domain.contracts.observation.observation_type import ObservationType
from domain.contracts.observation.observation_origin import ObservationOrigin


class ObservationTypeDistribution(BaseModel):
    """Count and share per ObservationType."""

    observation_type: ObservationType
    count: int = Field(..., ge=0)
    share: float = Field(..., ge=0.0, le=1.0)

    model_config = {"frozen": True, "extra": "forbid"}


class ObservationStatistics(BaseModel):
    """Descriptive statistics computed from a population of Observations.

    All fields are computed at construction via `from_observations()`.
    The object is immutable once built.

    Invariants:
    - total >= active + decayed + expired + superseded (equality when all statuses covered).
    - mean_confidence is None iff total == 0.
    - mean_weight is None iff total == 0.
    - type_distribution shares sum to ~1.0 when total > 0.
    """

    total: int = Field(default=0, ge=0)
    active_count: int = Field(default=0, ge=0)
    decayed_count: int = Field(default=0, ge=0)
    expired_count: int = Field(default=0, ge=0)
    superseded_count: int = Field(default=0, ge=0)

    mean_confidence: float | None = Field(default=None)
    min_confidence: float | None = Field(default=None)
    max_confidence: float | None = Field(default=None)

    mean_weight: float | None = Field(default=None)
    min_weight: float | None = Field(default=None)
    max_weight: float | None = Field(default=None)

    distinct_types: int = Field(default=0, ge=0)
    distinct_origins: int = Field(default=0, ge=0)
    distinct_question_indices: int = Field(default=0, ge=0)

    type_distribution: tuple[ObservationTypeDistribution, ...] = Field(default_factory=tuple)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_observations(cls, observations: list[Observation] | tuple[Observation, ...]) -> "ObservationStatistics":
        obs_seq = list(observations)
        total = len(obs_seq)

        if total == 0:
            return cls()

        active = sum(1 for o in obs_seq if o.status == ObservationStatus.ACTIVE)
        decayed = sum(1 for o in obs_seq if o.status == ObservationStatus.DECAYED)
        expired = sum(1 for o in obs_seq if o.status == ObservationStatus.EXPIRED)
        superseded = sum(1 for o in obs_seq if o.status == ObservationStatus.SUPERSEDED)

        confidences = [o.confidence for o in obs_seq]
        weights = [o.weight for o in obs_seq]

        type_counts: dict[ObservationType, int] = {}
        for o in obs_seq:
            type_counts[o.observation_type] = type_counts.get(o.observation_type, 0) + 1

        type_distribution = tuple(
            ObservationTypeDistribution(
                observation_type=t,
                count=c,
                share=round(c / total, 6),
            )
            for t, c in sorted(type_counts.items(), key=lambda x: -x[1])
        )

        return cls(
            total=total,
            active_count=active,
            decayed_count=decayed,
            expired_count=expired,
            superseded_count=superseded,
            mean_confidence=round(sum(confidences) / total, 6),
            min_confidence=min(confidences),
            max_confidence=max(confidences),
            mean_weight=round(sum(weights) / total, 6),
            min_weight=min(weights),
            max_weight=max(weights),
            distinct_types=len(type_counts),
            distinct_origins=len({o.metadata.origin for o in obs_seq}),
            distinct_question_indices=len({o.metadata.question_index for o in obs_seq}),
            type_distribution=type_distribution,
        )

    @property
    def active_share(self) -> float:
        if self.total == 0:
            return 0.0
        return self.active_count / self.total

    @property
    def is_empty(self) -> bool:
        return self.total == 0
