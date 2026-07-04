# domain/contracts/reasoning/reasoner_decision.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_signal import EvidenceSignal
from domain.contracts.reasoning.follow_up_recommendation import FollowUpRecommendation
from domain.contracts.reasoning.navigation_recommendation import NavigationRecommendation
from domain.contracts.reasoning.reasoning_basis import ReasoningBasis


class ReasonerDecision(BaseModel):
    """Fully structured output of one InterviewReasoner cycle (ADR-035).

    Contains no free-text fields.
    `skip=True` when Reasoner has insufficient context to reason
    (e.g. first question, no feedback bundle).

    `new_evidence` — EvidenceSignals detected this cycle only.
    `reasoning_basis` — structured provenance; consumed by NarrativeGenerator.
    """

    session_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)
    schema_version: str = Field(default="1.0")

    follow_up_recommendation: FollowUpRecommendation | None = None
    navigation_recommendation: NavigationRecommendation | None = None

    new_evidence: list[EvidenceSignal] = Field(default_factory=list)
    reasoning_basis: ReasoningBasis = Field(default_factory=ReasoningBasis)

    skip: bool = False

    model_config = {"frozen": True, "extra": "forbid"}
