# domain/contracts/reasoning/candidate_profile.py

from pydantic import BaseModel, Field

from domain.contracts.feature.profile_feature import ProfileFeature
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

    V1.2 (RS-02A, ADR-018, ADR-020): features carries the ProfileFeature[]
    produced by FeatureEngine for the most recent pipeline cycle.  Default
    is an empty tuple (backward-compatible).  Builder is the sole write path.
    """

    dimension_scores: dict[ProfileDimension, DimensionTrace] = Field(
        default_factory=dict
    )
    signals: dict[ProfileSignal, SignalTrace] = Field(default_factory=dict)
    questions_answered: int = Field(default=0, ge=0)
    areas_covered: list[str] = Field(default_factory=list)
    last_updated_at_question_index: int = Field(default=-1)
    # V1.2 (RS-02A): ProfileFeature[] from FeatureEngine; empty before first pipeline cycle.
    features: tuple[ProfileFeature, ...] = Field(default_factory=tuple)

    model_config = {"frozen": True, "extra": "forbid"}
