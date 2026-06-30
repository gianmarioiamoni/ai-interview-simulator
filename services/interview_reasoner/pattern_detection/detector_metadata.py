# services/interview_reasoner/pattern_detection/detector_metadata.py

from pydantic import BaseModel, Field


class DetectorMetadata(BaseModel):
    """Descriptor for a PatternDetector registration in PatternDetectorRegistry (ADR-045).

    The registry uses this metadata exclusively — no hardcoded if/else logic.

    Fields:
        name:         Unique identifier; must match ReasoningTraceStep.component.
        version:      Semver string (e.g. "1.0.0").
        priority:     Execution order within the pipeline — lower value runs first.
        enabled:      Registry checks this before invoking detect(). Feature-flag gate.
        dependencies: Names of detectors that must run before this one.
                      Registry validates all dependencies are registered and enabled.
    """

    name: str = Field(..., min_length=1, max_length=100)
    version: str = Field(default="1.0.0", min_length=1, max_length=20)
    priority: int = Field(default=100, ge=0)
    enabled: bool = True
    dependencies: list[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}
