# domain/contracts/reasoning/detector_context.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.pattern_match import PatternMatch
from domain.contracts.reasoning.reasoning_confidence import ReasoningConfidence
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
    """Uniform per-detector output contract (ADR-034, ADR-045).

    `matches`          — structured PatternMatch records produced this cycle.
    `generated_signals` — EvidenceSignals emitted (may be empty).
    `confidence`       — per-detector ReasoningConfidence snapshot.
    `execution_time_ms` — populated by the ReasonerService pipeline.
    `warnings`         — internal detector diagnostics; NEVER candidate-facing.
    """

    detector_name: str = Field(..., min_length=1)
    # Structured match records (one per detected pattern rule).
    matches: list[PatternMatch] = Field(default_factory=list)
    # Flat list of EvidenceSignal emitted by this detector this cycle.
    generated_signals: list[EvidenceSignal] = Field(default_factory=list)
    confidence: ReasoningConfidence = Field(default_factory=ReasoningConfidence)
    execution_time_ms: float = Field(default=0.0, ge=0.0)
    warnings: list[str] = Field(default_factory=list)

    model_config = {"frozen": True, "extra": "forbid"}
