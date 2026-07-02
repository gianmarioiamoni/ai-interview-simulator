# domain/contracts/observation/extraction/observation_extraction_result.py
# ADR-016: Extraction result — immutable output envelope

from pydantic import BaseModel, Field

from domain.contracts.observation.observation import Observation
from domain.contracts.observation.extraction.observation_extraction_diagnostics import ObservationExtractionDiagnostics


class ObservationExtractionResult(BaseModel):
    """Immutable output of one ObservationExtractor.extract() call.

    Contains the Observations produced from one extraction cycle and the
    associated diagnostics for audit and metrics.

    Invariants:
    - observations is ordered by (observation_type, confidence DESC) for
      deterministic downstream consumption.
    - question_index matches the extraction context.
    - session_id matches the extraction context.
    - diagnostics is always present; never None.
    """

    observations: tuple[Observation, ...] = Field(default_factory=tuple)
    question_index: int = Field(..., ge=0)
    session_id: str = Field(..., min_length=1)
    diagnostics: ObservationExtractionDiagnostics
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}

    @property
    def observation_count(self) -> int:
        return len(self.observations)

    @property
    def is_empty(self) -> bool:
        return len(self.observations) == 0
