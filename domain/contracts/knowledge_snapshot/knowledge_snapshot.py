# domain/contracts/knowledge_snapshot/knowledge_snapshot.py
# ADR-022 Section E — KnowledgeSnapshot (immutable closure artifact)

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.narrative.narrative import Narrative


class PolicyVersions(BaseModel):
    """Policy version bundle embedded in KnowledgeSnapshot (ADR-022 §E).

    All version fields are immutable strings — never inferred at runtime.
    """

    feature_engine_version: str = Field(
        ..., min_length=1, description="FeatureEngine schema/algorithm version"
    )
    language_policy_version: str = Field(
        ..., min_length=1, description="LanguagePolicy version (ADR-031)"
    )
    ttl_policy_version: str = Field(
        ..., min_length=1, description="TTL policy version"
    )
    evaluation_policy_version: str = Field(
        ..., min_length=1, description="EvaluationPolicy version"
    )
    narrative_schema_version: str = Field(
        ..., min_length=1, description="Narrative schema version (ADR-023)"
    )
    coaching_schema_version: str = Field(
        ..., min_length=1, description="Coaching schema version (ADR-025)"
    )
    profile_schema_version: str = Field(
        ..., min_length=1, description="CandidateProfileSnapshot schema version (ADR-032)"
    )

    model_config = {"frozen": True, "extra": "forbid"}


class KnowledgeSnapshot(BaseModel):
    """Immutable closure artifact produced at session close (ADR-022 §E).

    Assembles CandidateProfileSnapshot + Narrative + CoachingSnapshot + policy
    versions into a single sealed record. Cannot be modified after creation.

    ADR-022 invariants enforced:
    - K-01: Write-once — frozen=True
    - K-03: Policy versions always preserved
    - K-04: Knowledge epoch always recorded
    - K-07: snapshot_id is stable across the session lifetime
    - K-10: No references to live runtime objects

    KnowledgeEpoch (ADR-022 §I): generational marker V1.2 = "1".
    """

    snapshot_id: str = Field(
        ..., min_length=1, description="Stable unique identifier for this snapshot (K-07)"
    )
    session_id: str = Field(
        ..., min_length=1, description="Session that produced this snapshot"
    )
    candidate_identity_id: str = Field(
        ..., min_length=1, description="Owning candidate (ADR-016A)"
    )
    profile_snapshot: CandidateProfileSnapshot = Field(
        ..., description="Certified historical profile state at session close (ADR-032)"
    )
    narrative: Narrative = Field(
        ..., description="Immutable Narrative produced by NarrativeGenerator (ADR-023)"
    )
    coaching_snapshot: CoachingSnapshot = Field(
        ..., description="Assembled CoachingSnapshot: runtime coaching closure (ADR-025)"
    )
    policy_versions: PolicyVersions = Field(
        ..., description="All policy/schema versions in effect at closure (ADR-022 §E)"
    )
    knowledge_epoch: str = Field(
        default="1",
        description="Generational marker (ADR-022 §I). V1.2 = '1'. Never inferred."
    )
    created_at: datetime = Field(
        description="UTC timestamp of snapshot creation"
    )
    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Reserved extensibility metadata"
    )

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    @property
    def is_complete(self) -> bool:
        """True when all mandatory components are present — always True for valid KnowledgeSnapshot."""
        return True

    @property
    def feature_count(self) -> int:
        return self.profile_snapshot.total_feature_count

    @property
    def objective_count(self) -> int:
        return self.coaching_snapshot.statistics.total_objectives

    @property
    def insight_count(self) -> int:
        return self.narrative.insight_count
