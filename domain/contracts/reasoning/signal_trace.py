# domain/contracts/reasoning/signal_trace.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_polarity import EvidencePolarity
from domain.contracts.reasoning.trend import Trend

_MAX_OBSERVATIONS = 20


class SignalObservation(BaseModel):
    """One observed instance of a ProfileSignal at a specific question.

    `evidence` is a Reasoner-generated label — never interpolates candidate text
    (ADR-035 security constraint).
    """

    question_index: int = Field(..., ge=0)
    polarity: EvidencePolarity
    # Reasoner-generated descriptor; NEVER contains candidate-supplied text.
    evidence: str = Field(..., min_length=1, max_length=200)

    model_config = {"frozen": True, "extra": "forbid"}


class SignalTrace(BaseModel):
    """Running observation log for one ProfileSignal across the session.

    Capped at MAX_OBSERVATIONS (20) entries.
    """

    observations: list[SignalObservation] = Field(
        default_factory=list,
        max_length=_MAX_OBSERVATIONS,
    )
    trend: Trend = Trend.INSUFFICIENT_DATA

    model_config = {"frozen": True, "extra": "forbid"}
