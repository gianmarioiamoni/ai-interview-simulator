# domain/contracts/reasoning/reasoner_input.py

from __future__ import annotations

from pydantic import BaseModel, Field

from domain.contracts.reasoning.interview_memory import InterviewMemory


class ReasonerInput(BaseModel):
    """Single immutable input contract for InterviewReasoner (TDS §17.2).

    Built ONLY by ReasoningContextBuilder — no other component constructs
    ReasonerInput directly.

    `current_answer_content` is sanitized (max 2000 chars, control chars stripped)
    before placement here. This DTO never contains raw candidate text.

    Settings fields are snapshotted at construction time so the Reasoner
    sees a stable, consistent view of configuration for the entire cycle.
    """

    # --- Session identity ---
    session_id: str = Field(..., min_length=1)
    question_index: int = Field(..., ge=0)

    # --- Accumulated intelligence ---
    interview_memory: InterviewMemory = Field(default_factory=InterviewMemory)

    # --- Current cycle inputs ---
    current_question_area: str | None = None
    current_question_type: str | None = None
    # Sanitized; max 2000 chars; NEVER raw candidate text.
    current_answer_content: str | None = None
    # Quality.value string (e.g. "correct", "incorrect")
    current_feedback_quality: str | None = None
    current_dimension_signals: dict[str, float] = Field(default_factory=dict)
    # QuestionEvaluation score for current question, if available.
    current_evaluation_score: float | None = Field(default=None, ge=0.0, le=100.0)

    # --- Settings snapshot (frozen at construction) ---
    max_follow_ups: int = Field(default=2, ge=0)
    follow_up_count: int = Field(default=0, ge=0)
    follow_up_eligible_indices: frozenset[int] = Field(default_factory=frozenset)
    questions_remaining: int = Field(default=0, ge=0)

    # --- Interview metadata ---
    role: str = Field(default="")
    seniority: str = Field(default="mid")
    interview_type: str = Field(default="technical")

    model_config = {"frozen": True, "extra": "forbid"}
