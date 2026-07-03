# domain/contracts/knowledge_snapshot/knowledge_snapshot_statistics.py
# ADR-022 — KnowledgeSnapshotStatistics (aggregate metrics over a KnowledgeSnapshot)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.knowledge_snapshot.knowledge_snapshot import KnowledgeSnapshot


class KnowledgeSnapshotStatistics(BaseModel):
    """Aggregate metrics derived from a KnowledgeSnapshot.

    Pure computation — no LLM, no business logic, no mutation.
    Mirrors NarrativeStatistics / CoachingStatistics pattern.
    """

    total_features: int = Field(..., ge=0)
    total_objectives: int = Field(..., ge=0)
    total_actions: int = Field(..., ge=0)
    total_recommendations: int = Field(..., ge=0)
    total_narrative_insights: int = Field(..., ge=0)
    total_narrative_sections: int = Field(default=5, ge=0)

    mean_feature_confidence: float = Field(..., ge=0.0, le=1.0)
    mean_objective_confidence: float = Field(..., ge=0.0, le=1.0)
    mean_insight_confidence: float = Field(..., ge=0.0, le=1.0)

    unique_feature_type_ids: frozenset[str] = Field(default_factory=frozenset)

    knowledge_epoch: str = Field(..., min_length=1)
    profile_schema_version: str = Field(..., min_length=1)
    narrative_schema_version: str = Field(..., min_length=1)
    coaching_schema_version: str = Field(..., min_length=1)

    is_profile_empty: bool = Field(default=False)
    is_coaching_empty: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_snapshot(cls, snapshot: KnowledgeSnapshot) -> "KnowledgeSnapshotStatistics":
        """Compute statistics from a KnowledgeSnapshot. Pure derivation."""
        profile_snapshot = snapshot.profile_snapshot
        coaching_snapshot = snapshot.coaching_snapshot
        narrative = snapshot.narrative

        features = profile_snapshot.features
        mean_feature_conf = (
            sum(f.quality.confidence.value for f in features) / len(features)
            if features else 0.0
        )

        coaching_stats = coaching_snapshot.statistics
        insights = narrative.insights
        mean_insight_conf = (
            sum(i.confidence for i in insights) / len(insights)
            if insights else 0.0
        )

        return cls(
            total_features=profile_snapshot.total_feature_count,
            total_objectives=coaching_stats.total_objectives,
            total_actions=coaching_stats.total_actions,
            total_recommendations=coaching_stats.total_recommendations,
            total_narrative_insights=narrative.insight_count,
            total_narrative_sections=len(narrative.all_sections),
            mean_feature_confidence=mean_feature_conf,
            mean_objective_confidence=coaching_stats.mean_objective_confidence,
            mean_insight_confidence=mean_insight_conf,
            unique_feature_type_ids=profile_snapshot.feature_type_ids,
            knowledge_epoch=snapshot.knowledge_epoch,
            profile_schema_version=snapshot.policy_versions.profile_schema_version,
            narrative_schema_version=snapshot.policy_versions.narrative_schema_version,
            coaching_schema_version=snapshot.policy_versions.coaching_schema_version,
            is_profile_empty=profile_snapshot.is_empty,
            is_coaching_empty=coaching_stats.is_empty,
        )
