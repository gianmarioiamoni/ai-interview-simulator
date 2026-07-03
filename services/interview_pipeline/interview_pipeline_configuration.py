# services/interview_pipeline/interview_pipeline_configuration.py
# InterviewPipelineConfiguration — static pipeline settings

from __future__ import annotations

from pydantic import BaseModel, Field

from services.knowledge_pipeline.knowledge_pipeline_configuration import (
    KnowledgePipelineConfiguration,
)
from services.session_close.session_close_configuration import SessionCloseConfiguration


class InterviewPipelineConfiguration(BaseModel):
    """Immutable configuration for the InterviewPipeline.

    Aggregates sub-pipeline configurations and pipeline-level feature flags.

    Constraints:
    - No persistence references.
    - No LLM references.
    - No business logic.
    - Composed entirely of existing configuration contracts.
    """

    pipeline_version: str = Field(default="1.0.0", min_length=1)

    # Delegated sub-pipeline configurations (reuse existing contracts)
    knowledge_pipeline_configuration: KnowledgePipelineConfiguration = Field(
        default_factory=KnowledgePipelineConfiguration
    )
    session_close_configuration: SessionCloseConfiguration = Field(
        default_factory=SessionCloseConfiguration
    )

    # Pipeline-level abort behaviour
    abort_on_knowledge_pipeline_failure: bool = Field(
        default=True,
        description="When True, pipeline aborts if KnowledgePipeline fails.",
    )
    abort_on_narrative_failure: bool = Field(
        default=False,
        description="When True, pipeline aborts if NarrativeGenerator fails.",
    )
    abort_on_coaching_failure: bool = Field(
        default=False,
        description="When True, pipeline aborts if CoachingEngine fails.",
    )
    abort_on_session_close_failure: bool = Field(
        default=False,
        description="When True, pipeline aborts if SessionClosePipeline fails.",
    )

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid", "arbitrary_types_allowed": True}
