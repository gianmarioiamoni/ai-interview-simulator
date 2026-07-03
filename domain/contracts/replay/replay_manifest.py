# domain/contracts/replay/replay_manifest.py
# ADR-026 §D — ReplayManifest (runtime audit record of a replay operation)

from __future__ import annotations

from datetime import datetime, timezone

from pydantic import BaseModel, Field

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode, ReplaySourcePriority


class MigrationMetadata(BaseModel):
    """Metadata attached to MIGRATION or RECOVERY mode replays (ADR-026 §B5, MP-06).

    Present only when replay_mode is MIGRATION or RECOVERY.
    """

    trigger_reason: str = Field(..., min_length=1, description="Documented reason for migration")
    operator_id: str = Field(..., min_length=1, description="Human operator who triggered migration")
    feature_engine_version_used: str = Field(
        ..., min_length=1, description="FeatureEngine version used in reconstruction"
    )
    reconstruction_timestamp: datetime = Field(
        ..., description="UTC timestamp when reconstruction was executed"
    )
    is_reconstructed: bool = Field(
        default=True,
        description="Always True for migration outputs (ADR-026 §B5 MP-03)"
    )

    model_config = {"frozen": True, "extra": "forbid"}


class ReplayManifest(BaseModel):
    """Runtime audit record of a single replay operation (ADR-026 §D).

    Produced by ReplaySession at replay time. Not a stored domain object in V1.2;
    it is a runtime record logged for audit access.

    Invariants (SP-03, SP-04):
    - source_per_component records which priority level was used per component.
    - migration_metadata is present iff replay_mode is MIGRATION or RECOVERY.
    - replay_timestamp is always UTC.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    replay_mode: ReplayMode = Field(..., description="Standard, Migration, or Recovery")
    replay_level: ReplayLevel = Field(..., description="Level 1 or Level 2 (Level 3 reserved)")
    replay_timestamp: datetime = Field(..., description="UTC timestamp of the replay operation")
    replay_engine_version: str = Field(..., min_length=1)
    source_per_component: dict[str, ReplaySourcePriority] = Field(
        ...,
        description=(
            "Source priority used for each component (SP-03, SP-04). "
            "Keys: 'profile', 'narrative', 'coaching', 'policy_versions'."
        )
    )
    migration_metadata: MigrationMetadata | None = Field(
        default=None,
        description="Present only when replay_mode is MIGRATION or RECOVERY (MP-06)"
    )
    schema_version_notes: list[str] = Field(
        default_factory=list,
        description=(
            "Notes about schema version mismatches — display only, never modify values (RC-02)"
        )
    )
    reserved: dict[str, str] = Field(
        default_factory=dict,
        description="Reserved dict for future additive fields (ADR-026 §D)"
    )

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def for_standard_replay(
        cls,
        session_id: str,
        candidate_identity_id: str,
        replay_level: ReplayLevel,
        replay_engine_version: str,
        source_per_component: dict[str, ReplaySourcePriority],
        schema_version_notes: list[str] | None = None,
    ) -> "ReplayManifest":
        return cls(
            session_id=session_id,
            candidate_identity_id=candidate_identity_id,
            replay_mode=ReplayMode.STANDARD,
            replay_level=replay_level,
            replay_timestamp=datetime.now(tz=timezone.utc),
            replay_engine_version=replay_engine_version,
            source_per_component=source_per_component,
            migration_metadata=None,
            schema_version_notes=schema_version_notes or [],
        )
