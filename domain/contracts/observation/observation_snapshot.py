# domain/contracts/observation/observation_snapshot.py
# ADR-017: ObservationStore lifecycle — point-in-time snapshot
# ADR-021: Replay support — ordered snapshot for ReplayUpdater
# ADR-022: SessionHistory archival contract

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from domain.contracts.observation.observation import Observation


def _utcnow() -> datetime:
    return datetime.now(tz=timezone.utc)


class ObservationSnapshot(BaseModel):
    """Immutable point-in-time view of the ObservationStore for a single session.

    Produced by ObservationStore.snapshot(); consumed by FeatureEngine,
    ReplayUpdater, and SessionHistory archival pipeline.

    Invariants (ADR-017, ADR-021, ADR-022):
    - observations is ordered by question_index ASC (temporal ordering).
    - snapshotted_at is UTC.
    - session_id identifies the source session.
    - total_count == len(observations) for a full snapshot; may differ for
      filtered snapshots (active_count, decayed_count, expired_count provide
      breakdown).
    - No mutation after construction (frozen=True).
    """

    session_id: str = Field(..., min_length=1)
    observations: tuple[Observation, ...] = Field(default_factory=tuple)
    snapshotted_at: datetime = Field(default_factory=_utcnow)

    # Counts by status for fast telemetry without iterating observations.
    total_count: int = Field(default=0, ge=0)
    active_count: int = Field(default=0, ge=0)
    decayed_count: int = Field(default=0, ge=0)
    expired_count: int = Field(default=0, ge=0)
    superseded_count: int = Field(default=0, ge=0)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_observations(
        cls,
        session_id: str,
        observations: list[Observation],
    ) -> "ObservationSnapshot":
        """Build a snapshot from a list, computing status counts automatically."""
        from domain.contracts.observation.observation_status import ObservationStatus

        ordered = tuple(sorted(observations, key=lambda o: o.metadata.question_index))
        return cls(
            session_id=session_id,
            observations=ordered,
            total_count=len(ordered),
            active_count=sum(1 for o in ordered if o.status == ObservationStatus.ACTIVE),
            decayed_count=sum(1 for o in ordered if o.status == ObservationStatus.DECAYED),
            expired_count=sum(1 for o in ordered if o.status == ObservationStatus.EXPIRED),
            superseded_count=sum(1 for o in ordered if o.status == ObservationStatus.SUPERSEDED),
        )
