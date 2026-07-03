# domain/contracts/report/report_summary.py
# E03-M5 — ReportSummary (lightweight read-only view of a Report)
# ADR-023, ADR-025, ADR-032

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from domain.contracts.report.report import Report


class ReportSummary(BaseModel):
    """Lightweight, immutable summary view of a Report.

    Provides key aggregate properties without carrying full prose, feature data,
    or coaching payloads. Suitable for display, listing, logging, and monitoring.

    Mirrors KnowledgeSnapshotSummary / SessionHistorySummary pattern.
    Constraints:
    - No LLM, no FeatureEngine, no business logic, no mutation.
    - Immutable after construction (frozen=True).
    """

    report_id: str = Field(..., min_length=1)
    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    interview_index: int = Field(..., ge=0)

    role: str = Field(..., min_length=1)
    seniority: str = Field(..., min_length=1)
    interview_type: str = Field(..., min_length=1)
    question_count: int = Field(..., ge=0)

    knowledge_epoch: str = Field(..., min_length=1)
    schema_version: str = Field(..., min_length=1)
    created_at: datetime = Field(...)

    total_features: int = Field(..., ge=0)
    total_objectives: int = Field(..., ge=0)
    total_narrative_insights: int = Field(..., ge=0)
    mean_feature_confidence: float = Field(..., ge=0.0, le=1.0)

    is_profile_empty: bool = Field(default=False)
    is_coaching_empty: bool = Field(default=False)

    model_config = {"frozen": True, "extra": "forbid"}

    @classmethod
    def from_report(cls, report: Report) -> "ReportSummary":
        """Produce a lightweight summary from a Report. Pure derivation."""
        profile_snapshot = report.profile_snapshot
        features = profile_snapshot.features
        mean_feature_conf = (
            sum(f.quality.confidence.value for f in features) / len(features)
            if features else 0.0
        )

        return cls(
            report_id=report.report_id,
            session_id=report.session_id,
            candidate_identity_id=report.candidate_identity_id,
            interview_index=report.interview_index,
            role=report.role,
            seniority=report.seniority,
            interview_type=report.interview_type,
            question_count=report.question_count,
            knowledge_epoch=report.knowledge_epoch,
            schema_version=report.schema_version,
            created_at=report.created_at,
            total_features=profile_snapshot.total_feature_count,
            total_objectives=report.coaching_snapshot.statistics.total_objectives,
            total_narrative_insights=report.narrative.insight_count,
            mean_feature_confidence=mean_feature_conf,
            is_profile_empty=profile_snapshot.is_empty,
            is_coaching_empty=report.coaching_snapshot.statistics.is_empty,
        )
