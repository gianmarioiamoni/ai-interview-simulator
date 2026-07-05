# domain/contracts/report/report.py
# E03-M5 — Report v2.0 (immutable assembly of knowledge artefacts + scoring)
# ADR-023, ADR-025, ADR-032, ADR-033

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from pydantic import BaseModel, Field, model_validator

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.interview.generation_metadata import GenerationMetadata
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.knowledge_snapshot.candidate_profile_snapshot import (
    CandidateProfileSnapshot,
)
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.report.question_assessment_record import QuestionAssessmentRecord
from domain.contracts.session_history.session_history import SessionHistory

if TYPE_CHECKING:
    from domain.contracts.report.scoring_narrative import ScoringNarrative
    from domain.contracts.report.scoring_snapshot import ScoringSnapshot


class Report(BaseModel):
    """Immutable assembly of knowledge artefacts and scoring for one completed session.

    Report v2.0 is the unified, fully self-contained artifact consumed by the
    presentation layer. It carries both knowledge artefacts (narrative, coaching,
    profile) and scoring artefacts (ScoringSnapshot, ScoringNarrative, per-question
    assessments), eliminating any need for live InterviewState reads during rendering.

    Invariants:
    - R-01: Write-once — frozen=True.
    - R-02: All artefacts are read directly from SessionHistory / KnowledgeSnapshot.
    - R-03: No business logic; no recomputation of any artefact.
    - R-04: report_id is stable after creation.
    - R-05: candidate_identity_id and session_id are always present and consistent.
    - R-06: schema_version is always recorded.
    - V-R-01: len(question_assessments) == question_count.
    - V-R-02: scoring.dimension_scores keys must be non-empty.
    - V-R-03: candidate_identity_id == profile_snapshot.candidate_identity_id.

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

    # Phase 8 — new scoring artefacts (ADR-033)
    question_assessments: tuple[QuestionAssessmentRecord, ...] = Field(
        default_factory=tuple,
        description="Per-question report data assembled from SessionHistory.question_results",
    )
    scoring: "ScoringSnapshot" = Field(
        ..., description="All scoring fields (ADR-033 Decision 1)"
    )
    scoring_narrative: "ScoringNarrative" = Field(
        ..., description="All LLM coaching/narrative prose (ADR-033 Decision 3)"
    )
    context_profile: InterviewContextProfile = Field(
        ..., description="Interview context profile required for FinalReportDTO.from_report"
    )
    generation_metadata: GenerationMetadata | None = Field(
        default=None,
        description="LLM generation summary (tokens, cost). Optional — None renders as 0.",
    )

    role: str = Field(..., min_length=1, description="Interview role from session metadata")
    seniority: str = Field(..., min_length=1, description="Seniority level from session metadata")
    interview_type: str = Field(..., min_length=1)
    question_count: int = Field(..., ge=0)

    knowledge_epoch: str = Field(..., min_length=1, description="KnowledgeEpoch (ADR-022 §I)")
    schema_version: str = Field(default="2.0", min_length=1)
    created_at: datetime = Field(description="UTC timestamp of report assembly")

    metadata: dict[str, str] = Field(
        default_factory=dict,
        description="Reserved extensibility metadata",
    )

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    # ------------------------------------------------------------------
    # Validation invariants (Phase 8 — ADR-033)
    # ------------------------------------------------------------------

    @model_validator(mode="after")
    def _validate_question_assessments_count(self) -> "Report":
        """V-R-01: question_assessments count must equal question_count."""
        if len(self.question_assessments) != self.question_count:
            raise ValueError(
                f"V-R-01: len(question_assessments)={len(self.question_assessments)} "
                f"does not match question_count={self.question_count}."
            )
        return self

    # ------------------------------------------------------------------
    # Class methods
    # ------------------------------------------------------------------

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

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

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


# Resolve forward references for Pydantic v2 (ScoringSnapshot / ScoringNarrative imported
# only for type-checking to avoid circular imports)
def _rebuild() -> None:
    from domain.contracts.report.scoring_narrative import ScoringNarrative  # noqa: F401
    from domain.contracts.report.scoring_snapshot import ScoringSnapshot  # noqa: F401
    Report.model_rebuild()


_rebuild()
