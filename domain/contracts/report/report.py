# domain/contracts/report/report.py
# E03-M5 — Report (immutable assembly of existing knowledge artefacts)
# ADR-023, ADR-025, ADR-032

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.session_history.session_history import SessionHistory


class Report(BaseModel):
    """Immutable assembly of existing knowledge artefacts for one completed session.

    The Report layer assembles — never computes — knowledge.
    All components are sourced from a closed SessionHistory and its embedded
    KnowledgeSnapshot. No FeatureEngine, no LLM, no Replay, no persistence.

    Invariants:
    - R-01: Write-once — frozen=True.
    - R-02: All artefacts are read directly from SessionHistory / KnowledgeSnapshot.
    - R-03: No business logic; no recomputation of any artefact.
    - R-04: report_id is stable after creation.
    - R-05: candidate_identity_id and session_id are always present and consistent.
    - R-06: schema_version is always recorded.

    Creator: ReportBuilder (sole creation path).
    """

    report_id: str = Field(..., min_length=1, description="Stable unique identifier (R-04)")
    session_id: str = Field(..., min_length=1, description="Session this report covers (R-05)")
    candidate_identity_id: str = Field(..., min_length=1, description="Owning candidate (R-05)")
    interview_index: int = Field(..., ge=0, description="Sequential interview number (0-based)")

    profile_snapshot: CandidateProfileSnapshot = Field(
        ..., description="Historical profile state from KnowledgeSnapshot (ADR-032)"
    )
    narrative: Narrative = Field(
        ..., description="Stored Narrative from KnowledgeSnapshot (ADR-023)"
    )
    coaching_snapshot: CoachingSnapshot = Field(
        ..., description="Stored CoachingSnapshot from KnowledgeSnapshot (ADR-025)"
    )

    role: str = Field(..., min_length=1, description="Interview role from session metadata")
    seniority: str = Field(..., min_length=1, description="Seniority level from session metadata")
    interview_type: str = Field(..., min_length=1)
    question_count: int = Field(..., ge=0)

    knowledge_epoch: str = Field(..., min_length=1, description="KnowledgeEpoch (ADR-022 §I)")
    schema_version: str = Field(default="1.0", min_length=1)
    created_at: datetime = Field(description="UTC timestamp of report assembly")

    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Reserved extensibility metadata",
    )

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    @classmethod
    def from_session_history(cls, report_id: str, history: SessionHistory) -> "Report":
        """Assemble a Report from a closed SessionHistory via ReportBuilder.

        Delegates to ReportBuilder (sole creation path — PAT-05).
        """
        from domain.contracts.report.report_builder import ReportBuilder

        return (
            ReportBuilder()
            .with_session_history(history)
            .with_report_id(report_id)
            .build()
        )

    @property
    def feature_count(self) -> int:
        return self.profile_snapshot.total_feature_count

    @property
    def objective_count(self) -> int:
        return self.coaching_snapshot.statistics.total_objectives

    @property
    def insight_count(self) -> int:
        return self.narrative.insight_count

    @property
    def narrative_section_count(self) -> int:
        return len(self.narrative.all_sections)
