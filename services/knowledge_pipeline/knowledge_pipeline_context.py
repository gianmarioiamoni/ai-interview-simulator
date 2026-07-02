# services/knowledge_pipeline/knowledge_pipeline_context.py
# KnowledgePipelineContext — immutable execution context (E02-M5)

from pydantic import BaseModel, Field

from domain.contracts.reasoning.candidate_profile import CandidateProfile
from domain.contracts.reasoning.evidence_signal import EvidenceSignal


class KnowledgePipelineContext(BaseModel):
    """Immutable execution context for a single KnowledgePipeline invocation.

    Carries all inputs required to run one end-to-end pipeline cycle.

    Invariants:
    - session_id identifies the owning session; must be consistent with store.
    - candidate_identity_id identifies the candidate being profiled.
    - question_index >= 0; the position triggering this pipeline cycle.
    - signals is the set of EvidenceSignals for this cycle; may be empty only
      when configuration.allow_empty_signal_cycles is True.
    - prior_profile is the CandidateProfile from the previous cycle, or None
      when this is the first pipeline run.
    - No mutable infrastructure references are carried here.
    """

    session_id: str = Field(..., min_length=1)
    candidate_identity_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)
    signals: tuple[EvidenceSignal, ...] = Field(default_factory=tuple)
    prior_profile: CandidateProfile | None = Field(
        default=None,
        description="Profile from the preceding cycle, or None for the first cycle.",
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
