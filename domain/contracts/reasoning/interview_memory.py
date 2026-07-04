# domain/contracts/reasoning/interview_memory.py

from pydantic import BaseModel, Field

from domain.contracts.reasoning.coverage_state import CoverageState
from domain.contracts.reasoning.evidence_store import EvidenceStore
from domain.contracts.reasoning.reasoning_history import ReasoningHistory
from domain.contracts.reasoning.session_metrics import SessionMetrics


class InterviewMemory(BaseModel):
    """Session-scoped accumulated intelligence owned by InterviewReasoner.

    Composed of four independent immutable substructures (ADR-038).
    Supersedes InterviewMemoryContext (deprecated M2, removed M3, ADR-032).

    Single-writer: InterviewReasoner.
    All other components read it; none write to it directly.
    """

    evidence_store: EvidenceStore = Field(
        default_factory=EvidenceStore
    )
    coverage_state: CoverageState = Field(
        default_factory=CoverageState
    )
    reasoning_history: ReasoningHistory = Field(
        default_factory=ReasoningHistory
    )
    session_metrics: SessionMetrics = Field(
        default_factory=SessionMetrics
    )
    schema_version: str = Field(default="1.0")

    model_config = {"frozen": True, "extra": "forbid"}
