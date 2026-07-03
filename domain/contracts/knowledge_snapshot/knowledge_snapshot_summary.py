# domain/contracts/knowledge_snapshot/knowledge_snapshot_summary.py
# ADR-022 — KnowledgeSnapshotSummary (lightweight read-only view of a KnowledgeSnapshot)

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot


class KnowledgeSnapshotSummary(BaseModel):
    """Lightweight, immutable summary view of a KnowledgeSnapshot.

    Provides key aggregate properties without carrying full prose, feature data,
    or coaching payloads. Suitable for display, logging, and monitoring.

    Mirrors NarrativeSummary pattern (ADR-023) at the snapshot layer.
    Constraints:
    - No LLM, no business logic, no mutation.
    - Immutable after construction (frozen=True).
    """

    snapshot_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    knowledge_epoch: str = Field(..., min_length=1)
    created_at: datetime = Field(...)

    total_features: int = Field(..., ge=0)
    total_objectives: int = Field(..., ge=0)
    total_narrative_insights: int = Field(..., ge=0)

    mean_feature_confidence: float = Field(..., ge=0.0, le=1.0)

    profile_schema_version: str = Field(..., min_length=1)
    narrative_schema_version: str = Field(..., min_length=1)
    coaching_schema_version: str = Field(..., min_length=1)

    is_profile_empty: bool = Field(default=False)
    is_coaching_empty: bool = Field(default=False)
    is_complete: bool = Field(default=True)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_snapshot(cls, snapshot: KnowledgeSnapshot) -> "KnowledgeSnapshotSummary":
        """Produce a lightweight summary from a KnowledgeSnapshot. Pure derivation."""
        profile_snapshot = snapshot.profile_snapshot
        features = profile_snapshot.features
        mean_feature_conf = (
            sum(f.quality.confidence.value for f in features) / len(features)
            if features else 0.0
        )

        coaching_stats = snapshot.coaching_snapshot.statistics

        return cls(
            snapshot_id=snapshot.snapshot_id,
            session_id=snapshot.session_id,
            candidate_identity_id=snapshot.candidate_identity_id,
            knowledge_epoch=snapshot.knowledge_epoch,
            created_at=snapshot.created_at,
            total_features=profile_snapshot.total_feature_count,
            total_objectives=coaching_stats.total_objectives,
            total_narrative_insights=snapshot.narrative.insight_count,
            mean_feature_confidence=mean_feature_conf,
            profile_schema_version=snapshot.policy_versions.profile_schema_version,
            narrative_schema_version=snapshot.policy_versions.narrative_schema_version,
            coaching_schema_version=snapshot.policy_versions.coaching_schema_version,
            is_profile_empty=profile_snapshot.is_empty,
            is_coaching_empty=coaching_stats.is_empty,
            is_complete=snapshot.is_complete,
        )
