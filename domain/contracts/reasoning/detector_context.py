# domain/contracts/reasoning/detector_context.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.reasoner_input import ReasonerInput


class DetectorContext(BaseModel):
    """Thin wrapper passed to each PatternDetector by the pipeline.

    Carries the full ReasonerInput plus the detector's name for trace
    labelling. Detectors are stateless and receive only this context.
    """

    detector_name: str = Field(..., min_length=1)
    input: ReasonerInput

    model_config = {"frozen": True, "extra": "forbid"}


class DetectorResult(BaseModel):
    """Output of one PatternDetector.detect() call.

    `execution_time_ms` is populated by the pipeline, not the detector.
    """

    detector_name: str = Field(..., min_length=1)
    evidence: list[EvidenceSignal] = Field(default_factory=list)
    execution_time_ms: float = Field(default=0.0, ge=0.0)

    model_config = {"frozen": True, "extra": "forbid"}
