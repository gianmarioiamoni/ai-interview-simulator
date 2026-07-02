# domain/observation/runtime/observation_delta.py
# Structural diff between two Observation populations (e.g., two snapshots).

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.observation_id import ObservationId
from domain.contracts.observation.observation_status import ObservationStatus


class ObservationDelta(BaseModel):
    """Diff between a baseline and a revised Observation population.

    Captures:
    - added:      present in revised, absent in baseline.
    - removed:    present in baseline, absent in revised.
    - superseded: present in both; status changed to SUPERSEDED in revised.
    - expired:    present in both; status changed to EXPIRED in revised.

    Invariants:
    - All sets are disjoint by observation id.
    - No mutation after construction (frozen=True).
    """

    added: tuple[Observation, ...] = Field(default_factory=tuple)
    removed: tuple[Observation, ...] = Field(default_factory=tuple)
    superseded: tuple[Observation, ...] = Field(default_factory=tuple)
    expired: tuple[Observation, ...] = Field(default_factory=tuple)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def compute(
        cls,
        baseline: list[Observation] | tuple[Observation, ...],
        revised: list[Observation] | tuple[Observation, ...],
    ) -> "ObservationDelta":
        """Compute the delta from baseline to revised.

        Identity is tracked by ObservationId. Status transitions are classified:
        - ACTIVE in baseline → SUPERSEDED in revised  → superseded bucket
        - ACTIVE in baseline → EXPIRED in revised      → expired bucket
        - absent in baseline, present in revised       → added bucket
        - present in baseline, absent in revised       → removed bucket
        """
        baseline_by_id: dict[str, Observation] = {o.id.value: o for o in baseline}
        revised_by_id: dict[str, Observation] = {o.id.value: o for o in revised}

        baseline_ids = set(baseline_by_id)
        revised_ids = set(revised_by_id)

        added_ids = revised_ids - baseline_ids
        removed_ids = baseline_ids - revised_ids
        common_ids = baseline_ids & revised_ids

        superseded: list[Observation] = []
        expired: list[Observation] = []

        for oid in common_ids:
            base_obs = baseline_by_id[oid]
            rev_obs = revised_by_id[oid]
            if (
                base_obs.status == ObservationStatus.ACTIVE
                and rev_obs.status == ObservationStatus.SUPERSEDED
            ):
                superseded.append(rev_obs)
            elif (
                base_obs.status != ObservationStatus.EXPIRED
                and rev_obs.status == ObservationStatus.EXPIRED
            ):
                expired.append(rev_obs)

        return cls(
            added=tuple(revised_by_id[oid] for oid in sorted(added_ids)),
            removed=tuple(baseline_by_id[oid] for oid in sorted(removed_ids)),
            superseded=tuple(superseded),
            expired=tuple(expired),
        )

    @property
    def is_empty(self) -> bool:
        return (
            not self.added
            and not self.removed
            and not self.superseded
            and not self.expired
        )

    @property
    def total_changes(self) -> int:
        return len(self.added) + len(self.removed) + len(self.superseded) + len(self.expired)

    def added_ids(self) -> frozenset[ObservationId]:
        return frozenset(o.id for o in self.added)

    def removed_ids(self) -> frozenset[ObservationId]:
        return frozenset(o.id for o in self.removed)
