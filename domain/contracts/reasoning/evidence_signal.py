# domain/contracts/reasoning/evidence_signal.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.evidence_source import EvidenceSource
from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension


class EvidenceSignal(BaseModel):
    """Atomic unit of observed candidate evidence for one dimension in one question.

    Both positive and negative evidence are represented via `polarity`.
    Captured by PatternDetectors and the EvaluationNode signal pipeline.

    Rules (ADR-033, ADR-035):
    - `id` is a uuid4 string assigned at creation time.
    - `schema_version` enables forward-compatible deserialization.
    - `timestamp_question_index` mirrors `question_index` and is retained for
      deterministic replay ordering when future persistence is introduced.
    - This DTO never contains candidate-supplied text.
    """

    id: str = Field(..., min_length=1, description="uuid4 assigned at creation")
    question_index: int = Field(..., ge=0)
    question_area: str = Field(..., min_length=1)
    dimension: ProfileDimension
    polarity: EvidencePolarity
    signal_type: EvidenceType
    strength: float = Field(..., ge=0.0, le=1.0)
    source: EvidenceSource
    schema_version: str = Field(default="1.0")
    # Retained for replay ordering; mirrors question_index (ADR-033).
    timestamp_question_index: int = Field(..., ge=0)

    model_config = {"frozen": True, "extra": "forbid"}
