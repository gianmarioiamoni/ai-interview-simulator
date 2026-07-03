# services/interview_pipeline/interview_pipeline_context.py
# InterviewPipelineContext — immutable input bundle for one InterviewPipeline invocation

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.feature.feature_collection import FeatureCollection
from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_signal import EvidenceSignal


class InterviewPipelineContext(BaseModel):
    """Immutable input bundle for a single InterviewPipeline invocation.

    Carries all read-only inputs required to drive the full interview pipeline.

    Invariants:
    - session_id and candidate_identity_id must be consistent across all stages.
    - question_index >= 0; identifies the pipeline cycle.
    - signals are pre-collected EvidenceSignals for this cycle.
    - prior_profile is None on the first cycle; non-None on subsequent cycles.
    - No mutable infrastructure references are carried here.
    - No LLM, Persistence, Replay, or SessionHistory references.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    signals: tuple[EvidenceSignal, ...] = Field(
        default_factory=tuple,
        description="EvidenceSignals for this pipeline cycle; may be empty.",
    )
    prior_profile: CandidateProfile | None = Field(
        default=None,
        description="CandidateProfile from the preceding cycle; None on first cycle.",
    )
    prior_features: FeatureCollection | None = Field(
        default=None,
        description="FeatureCollection from the preceding cycle; None on first cycle.",
    )

    # Interview metadata passed through to downstream stages
    interview_topic: str | None = Field(default=None)
    interview_role: str | None = Field(default=None)
    knowledge_gap_observation_ids: tuple[str, ...] = Field(default_factory=tuple)
    evaluation_summary: dict[str, str] = Field(default_factory=dict)
    interview_metadata: dict[str, str] = Field(default_factory=dict)

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}
