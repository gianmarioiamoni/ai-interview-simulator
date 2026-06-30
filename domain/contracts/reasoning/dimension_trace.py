# domain/contracts/reasoning/dimension_trace.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.trend import Trend


class DimensionTrace(BaseModel):
    """Running aggregate for one ProfileDimension across the session.

    Stores only derived aggregates — NOT the raw per-question scores.
    Raw scores already exist in `state.results_by_question[q_id].evaluation`
    and must not be duplicated here (ADR-037).
    """

    average_score: float = Field(default=0.0, ge=0.0, le=100.0)
    last_score: float | None = Field(default=None, ge=0.0, le=100.0)
    trend: Trend = Trend.INSUFFICIENT_DATA
    # evidence_count / questions_answered, capped at 1.0
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_count: int = Field(default=0, ge=0)
    last_updated_question: int = Field(default=-1)

    model_config = {"frozen": True, "extra": "forbid"}
