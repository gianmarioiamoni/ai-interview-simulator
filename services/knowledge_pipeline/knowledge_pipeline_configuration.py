# services/knowledge_pipeline/knowledge_pipeline_configuration.py
# KnowledgePipelineConfiguration — static pipeline settings (E02-M5)

from pydantic import BaseModel, Field


class KnowledgePipelineConfiguration(BaseModel):
    """Immutable configuration for the KnowledgePipeline.

    Controls stage-level behaviour without owning business logic.
    All options are optional with safe defaults.

    Constraints:
    - No persistence references.
    - No LLM references.
    - No Narrative / Coaching / Replay / SessionHistory references.
    """

    pipeline_version: str = Field(default="1.0.0", min_length=1)

    # Whether the pipeline should continue when a single stage fails
    # (soft failure) or abort immediately (hard failure).
    abort_on_stage_failure: bool = Field(
        default=False,
        description="When True, any stage failure aborts the pipeline immediately.",
    )

    # Extractor version passed into ObservationExtractionContext
    extractor_version: str = Field(default="1.0", min_length=1)

    # FeatureEngine version passed into FeatureEngineContext
    feature_engine_version: str = Field(default="1.0.0", min_length=1)

    # Whether to emit empty-signal cycles through the extraction stage.
    # When False, an empty signal list short-circuits extraction.
    allow_empty_signal_cycles: bool = Field(
        default=False,
        description="When True, extraction proceeds even with zero EvidenceSignals.",
    )

    # MIG-02.5: when True, Stage 1 (ObservationExtractor) is skipped if the
    # ObservationStore passed into the pipeline already contains observations.
    # This prevents double extraction when reasoner_node has already run
    # ObservationExtractor during Phase C (MIG-02A).
    # The pipeline still executes Stages 3–5 (snapshot → FeatureEngine → ProfileBuild).
    skip_extraction_if_store_populated: bool = Field(
        default=False,
        description=(
            "When True, skip extraction Stage 1 if the store already has observations. "
            "Prevents double extraction when ObservationExtractor ran in reasoner_node."
        ),
    )

    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
