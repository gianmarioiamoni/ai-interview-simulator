# domain/contracts/replay/replay_result.py
# ADR-026 §B6 — ReplayResult (output of a replay operation)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.knowledge_snapshot.knowledge_snapshot import PolicyVersions
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode
from domain.contracts.replay.replay_manifest import ReplayManifest


class ReplayResult(BaseModel):
    """Immutable output of a completed replay operation (ADR-026 §B6).

    Contains all components assembled by ReplaySession from KnowledgeSnapshot.
    No live pipeline component is invoked to produce any field (RC-03).

    Consistency guarantees enforced (ADR-026 §B4):
    - RC-01: All components read from stored KnowledgeSnapshot.
    - RC-02: No silent schema upgrades — schema_version_mismatch_noted flags if noted.
    - RC-03: No on-the-fly calculations; every value is a direct read.
    - RC-04: profile_schema_version carries historical interpretation key.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    replay_mode: ReplayMode
    replay_level: ReplayLevel

    profile_snapshot: CandidateProfileSnapshot = Field(
        ..., description="Historical profile state at session close (ADR-032)"
    )
    narrative: Narrative = Field(
        ..., description="Stored narrative — never recomputed (RC-03)"
    )
    coaching_snapshot: CoachingSnapshot = Field(
        ..., description="Stored coaching plan — never recomputed (RC-03)"
    )
    policy_versions: PolicyVersions = Field(
        ..., description="Policy versions in effect at session close (ADR-026 §B2)"
    )
    knowledge_epoch: str = Field(
        ..., min_length=1, description="KnowledgeEpoch for this snapshot (ADR-022 §I)"
    )

    manifest: ReplayManifest = Field(
        ..., description="Audit record for this replay operation (SP-03, ADR-026 §D)"
    )

    is_successful: bool = Field(default=True)
    failure_reason: str | None = Field(
        default=None,
        description="Non-None only when is_successful=False"
    )

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    @property
    def is_standard(self) -> bool:
        return self.replay_mode == ReplayMode.STANDARD

    @property
    def has_provenance_access(self) -> bool:
        """True when replay_level is KNOWLEDGE — provenance is available (ADR-026 §B3)."""
        return self.replay_level == ReplayLevel.KNOWLEDGE
