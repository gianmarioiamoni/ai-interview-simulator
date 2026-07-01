# domain/contracts/reasoning/candidate_profile.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.dimension_trace import DimensionTrace
from domain.contracts.reasoning.profile_dimension import ProfileDimension
from domain.contracts.reasoning.profile_signal import ProfileSignal
from domain.contracts.reasoning.signal_trace import SignalTrace


class CandidateProfile(BaseModel):
    """Evolving candidate assessment updated by InterviewReasoner each cycle.

    Owned exclusively by InterviewReasoner (single-writer, ADR-037).
    Lives inside InterviewMemory (ADR-038).

    Raw per-question scores are NOT stored here — they exist in
    `state.results_by_question`. Only derived aggregates are kept.
    """

    dimension_scores: dict[ProfileDimension, DimensionTrace] = Field(
        default_factory=dict
    )
    # TODO(V1.2): signals is reserved for the ProfileFeature layer (ADR-039).
    # Not populated or read in V1.1. Will be activated when the Observation
    # Layer and ProfileFeature mapping are introduced in V1.2.
    signals: dict[ProfileSignal, SignalTrace] = Field(default_factory=dict)
    questions_answered: int = Field(default=0, ge=0)
    areas_covered: list[str] = Field(default_factory=list)
    last_updated_at_question_index: int = Field(default=-1)

    model_config = {"frozen": True, "extra": "forbid"}
