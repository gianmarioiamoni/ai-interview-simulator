# domain/contracts/session_history/session_history_statistics.py
# ADR-022 — SessionHistoryStatistics (aggregate metrics over a SessionHistory)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.session_history.session_history import SessionHistory


class SessionHistoryStatistics(BaseModel):
    """Aggregate metrics derived from a SessionHistory.

    Pure computation — no LLM, no business logic, no mutation.
    Mirrors KnowledgeSnapshotStatistics pattern at the session layer.

    Derives knowledge metrics via the embedded KnowledgeSnapshot and adds
    session-level metrics (question count, transcript coverage, timeline coverage).
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    interview_index: int = Field(..., ge=0)

    question_count: int = Field(..., ge=0, description="Total questions in transcript")
    timeline_entry_count: int = Field(..., ge=0, description="Entries in question_timeline")
    has_evaluation: bool = Field(default=False)

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
    schema_version: str = Field(..., min_length=1)
    profile_schema_version: str = Field(..., min_length=1)
    narrative_schema_version: str = Field(..., min_length=1)
    coaching_schema_version: str = Field(..., min_length=1)

    is_profile_empty: bool = Field(default=False)
    is_coaching_empty: bool = Field(default=False)
    is_replay_ready: bool = Field(default=True)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_history(cls, history: SessionHistory) -> "SessionHistoryStatistics":
        """Compute statistics from a SessionHistory. Pure derivation."""
        snapshot = history.knowledge_snapshot
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
            session_id=history.session_id,
            candidate_identity_id=history.candidate_identity_id,
            interview_index=history.interview_index,
            question_count=history.question_count,
            timeline_entry_count=len(history.question_timeline),
            has_evaluation=history.scoring_snapshot is not None,
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
            knowledge_epoch=history.knowledge_epoch,
            schema_version=history.schema_version,
            profile_schema_version=snapshot.policy_versions.profile_schema_version,
            narrative_schema_version=snapshot.policy_versions.narrative_schema_version,
            coaching_schema_version=snapshot.policy_versions.coaching_schema_version,
            is_profile_empty=profile_snapshot.is_empty,
            is_coaching_empty=coaching_stats.is_empty,
            is_replay_ready=history.is_replay_ready,
        )
