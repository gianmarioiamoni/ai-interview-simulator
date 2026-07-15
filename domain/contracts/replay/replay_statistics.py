# domain/contracts/replay/replay_statistics.py
# ADR-026 §B3, §B4 — ReplayStatistics (aggregate metrics over a ReplaySession V1.3)
# V1.3: from_result deleted; from_session added (Data Model §12.2).

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, Field

from domain.contracts.replay.replay_enums import ReplayLevel, ReplayMode, ReplaySourcePriority

if TYPE_CHECKING:
    from domain.contracts.replay.replay_session import ReplaySession


class ReplayStatistics(BaseModel):
    """Aggregate metrics derived from a completed ReplaySession (V1.3).

    Pure derivation — no pipeline invocation, no mutation (RC-03).
    Mirrors KnowledgeSnapshotStatistics pattern.
    """

    session_id: str = Field(..., min_length=1)
    replay_mode: ReplayMode
    replay_level: ReplayLevel

    total_features: int = Field(..., ge=0)
    total_objectives: int = Field(..., ge=0)
    total_actions: int = Field(..., ge=0)
    total_recommendations: int = Field(..., ge=0)
    total_narrative_insights: int = Field(..., ge=0)
    total_narrative_sections: int = Field(..., ge=0)
    total_source_observation_ids: int = Field(..., ge=0)

    mean_feature_confidence: float = Field(..., ge=0.0, le=1.0)

    unique_feature_type_ids: frozenset[str] = Field(default_factory=frozenset)

    knowledge_epoch: str = Field(..., min_length=1)
    profile_schema_version: str = Field(..., min_length=1)
    narrative_schema_version: str = Field(..., min_length=1)
    coaching_schema_version: str = Field(..., min_length=1)

    primary_source_used: ReplaySourcePriority = Field(
        ..., description="Highest priority source level consumed (SP-01)"
    )
    is_standard_mode: bool = Field(..., description="True iff replay_mode == STANDARD")
    is_profile_empty: bool = Field(default=False)

    # V1.3 additions (from_session)
    question_count: int = Field(default=0, ge=0)
    has_scoring: bool = Field(default=False)
    total_follow_up_questions: int = Field(default=0, ge=0)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_session(cls, session: "ReplaySession") -> "ReplayStatistics":
        """Derive statistics from a V1.3 ReplaySession (replaces from_result after migration).

        New fields per Data Model §12.2: question_count, has_scoring, total_follow_up_questions.
        """
        profile = session.profile_snapshot
        coaching = session.coaching_snapshot
        narrative = session.narrative
        pv = session.policy_versions

        features = profile.features
        mean_conf = (
            sum(f.quality.confidence.value for f in features) / len(features)
            if features else 0.0
        )

        coaching_stats = coaching.statistics

        profile_source = session.manifest.source_per_component.get(
            "profile", ReplaySourcePriority.KNOWLEDGE_SNAPSHOT
        )

        total_follow_up = sum(
            1 for qr in session.question_results if qr.follow_up_question is not None
        )

        return cls(
            session_id=session.session_id,
            replay_mode=session.replay_mode,
            replay_level=session.replay_level,
            total_features=profile.total_feature_count,
            total_objectives=coaching_stats.total_objectives,
            total_actions=coaching_stats.total_actions,
            total_recommendations=coaching_stats.total_recommendations,
            total_narrative_insights=narrative.insight_count,
            total_narrative_sections=len(narrative.all_sections),
            total_source_observation_ids=len(profile.source_observation_ids),
            mean_feature_confidence=mean_conf,
            unique_feature_type_ids=profile.feature_type_ids,
            knowledge_epoch=session.knowledge_epoch,
            profile_schema_version=pv.profile_schema_version,
            narrative_schema_version=pv.narrative_schema_version,
            coaching_schema_version=pv.coaching_schema_version,
            primary_source_used=profile_source,
            is_standard_mode=session.replay_mode == ReplayMode.STANDARD,
            is_profile_empty=profile.is_empty,
            question_count=len(session.question_results),
            has_scoring=session.scoring_snapshot is not None,
            total_follow_up_questions=total_follow_up,
        )
