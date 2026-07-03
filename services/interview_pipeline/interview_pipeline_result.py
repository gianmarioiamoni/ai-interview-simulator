# services/interview_pipeline/interview_pipeline_result.py
# InterviewPipelineResult — immutable output of InterviewPipeline

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.coaching.coaching_builder import CoachingSnapshot
from domain.contracts.narrative.narrative import Narrative
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.session_history.session_history import SessionHistory
from services.interview_pipeline.interview_pipeline_diagnostics import (
    InterviewPipelineDiagnostics,
)


class InterviewPipelineResult(BaseModel):
    """Immutable output of a single InterviewPipeline run.

    Contains the aggregated outputs from all pipeline stages and full
    diagnostics for this invocation.

    Invariants:
    - diagnostics is always present regardless of success/failure.
    - failure_reason is non-None only when is_successful is False.
    - profile, narrative, coaching_snapshot, session_history may be None
      when the corresponding stage did not complete successfully.
    - No persistence references; caller decides what to do with outputs.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    profile: CandidateProfile | None = Field(
        default=None,
        description="Updated CandidateProfile; None when KnowledgePipeline did not complete.",
    )
    narrative: Narrative | None = Field(
        default=None,
        description="Generated Narrative; None when NarrativeGenerator failed or was skipped.",
    )
    coaching_snapshot: CoachingSnapshot | None = Field(
        default=None,
        description="Assembled CoachingSnapshot; None when CoachingEngine failed or was skipped.",
    )
    session_history: SessionHistory | None = Field(
        default=None,
        description="Assembled SessionHistory; None when SessionClosePipeline failed or was skipped.",
    )

    diagnostics: InterviewPipelineDiagnostics = Field(
        ..., description="Full audit trail for this pipeline run."
    )
    is_successful: bool = Field(default=True)
    failure_reason: str | None = Field(default=None)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}

    @property
    def has_profile(self) -> bool:
        return self.profile is not None

    @property
    def has_narrative(self) -> bool:
        return self.narrative is not None

    @property
    def has_coaching(self) -> bool:
        return self.coaching_snapshot is not None

    @property
    def has_session_history(self) -> bool:
        return self.session_history is not None

    @property
    def stages_completed(self) -> int:
        return sum(
            1
            for r in self.diagnostics.stage_records
            if r.completed
        )
