# services/knowledge_pipeline/knowledge_pipeline_result.py
# KnowledgePipelineResult — immutable pipeline output (E02-M5)

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.feature.profile_feature import ProfileFeature
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from services.knowledge_pipeline.knowledge_pipeline_diagnostics import KnowledgePipelineDiagnostics


class KnowledgePipelineResult(BaseModel):
    """Immutable output of a single KnowledgePipeline run.

    Contains the updated CandidateProfile, computed features, and full
    diagnostics for this cycle.

    Invariants:
    - profile is None only when is_successful is False and pipeline aborted
      before the profile-build stage completed.
    - features is empty when the FeatureEngine stage produced no output
      or was not reached.
    - diagnostics is always present regardless of success/failure.
    - failure_reason is non-None only when is_successful is False.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    profile: CandidateProfile | None = Field(
        default=None,
        description="Updated CandidateProfile; None when pipeline did not complete profile build.",
    )
    features: tuple[ProfileFeature, ...] = Field(
        default_factory=tuple,
        description="Features computed by FeatureEngine in this cycle.",
    )
    diagnostics: KnowledgePipelineDiagnostics = Field(
        ..., description="Full audit trail for this pipeline run."
    )
    is_successful: bool = Field(default=True)
    failure_reason: str | None = Field(default=None)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def has_profile(self) -> bool:
        return self.profile is not None

    @property
    def feature_count(self) -> int:
        return len(self.features)
