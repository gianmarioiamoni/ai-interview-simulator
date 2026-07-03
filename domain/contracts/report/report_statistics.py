# domain/contracts/report/report_statistics.py
# E03-M5 — ReportStatistics (aggregate metrics over a Report)
# ADR-023, ADR-025, ADR-032

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.report.report import Report


class ReportStatistics(BaseModel):
    """Aggregate metrics derived from a Report.

    Pure derivation — no LLM, no FeatureEngine, no business logic, no mutation.
    Mirrors KnowledgeSnapshotStatistics / SessionHistoryStatistics / ReplayStatistics pattern.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    interview_index: int = Field(..., ge=0)

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

    question_count: int = Field(..., ge=0)
    knowledge_epoch: str = Field(..., min_length=1)
    schema_version: str = Field(..., min_length=1)

    is_profile_empty: bool = Field(default=False)
    is_coaching_empty: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_report(cls, report: Report) -> "ReportStatistics":
        """Compute statistics from a Report. Pure derivation."""
        profile_snapshot = report.profile_snapshot
        coaching_snapshot = report.coaching_snapshot
        narrative = report.narrative

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
            session_id=report.session_id,
            candidate_identity_id=report.candidate_identity_id,
            interview_index=report.interview_index,
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
            question_count=report.question_count,
            knowledge_epoch=report.knowledge_epoch,
            schema_version=report.schema_version,
            is_profile_empty=profile_snapshot.is_empty,
            is_coaching_empty=coaching_stats.is_empty,
        )
