# domain/contracts/reasoning/reasoning_history.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.evidence_type import EvidenceType
from domain.contracts.reasoning.profile_dimension import ProfileDimension

_MAX_ENTRIES = 20


class ReasoningEntry(BaseModel):
    """Compact per-cycle record stored in ReasoningHistory.

    Contains only structured metadata — no free text (ADR-035).
    `schema_version` enables forward-compatible replay (ADR-041).
    """

    question_index: int = Field(..., ge=0)
    dominant_dimension: ProfileDimension | None = None
    detected_patterns: list[EvidenceType] = Field(default_factory=list)
    follow_up_recommended: bool = False
    navigation_recommended: bool = False
    reasoning_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}


class ReasoningHistory(BaseModel):
    """Bounded log of ReasoningEntry records — one per answered question.

    Capped at MAX_ENTRIES (20).
    Used for debugging, architecture audits, and future replay (ADR-041).
    Single-writer: InterviewReasoner (ADR-038).
    """

    entries: list[ReasoningEntry] = Field(
        default_factory=list,
        max_length=_MAX_ENTRIES,
    )

    model_config = {"frozen": True, "extra": "forbid"}
