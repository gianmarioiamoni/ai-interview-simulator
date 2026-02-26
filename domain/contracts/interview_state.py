# domain/contracts/interview_state.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, model_validator

from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.role import Role
from domain.contracts.interview_evaluation import InterviewEvaluation


class InterviewState(BaseModel):

    # minimal setup already validated in Phase 1
    interview_id: str = Field(..., min_length=1)
    role: Role
    company: str = Field(..., min_length=1)
    language: str = Field(default="en")

    # progress tracking
    progress: InterviewProgress = Field(default=InterviewProgress.SETUP)
    questions: list[Question] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
    evaluations: list[QuestionEvaluation] = Field(default_factory=list)
    final_evaluation: Optional[InterviewEvaluation] = None

    # conversational memory for humanizer
    chat_history: list[str] = Field(default_factory=list)

    # pointer to the current question
    current_question_id: Optional[str] = None

    # governance follow-up
    follow_up_count: int = Field(default=0, ge=0, le=2)

    # execution engines
    execution_results: list[ExecutionResult] = Field(default_factory=list)

    # runtime orchestration state for LangGraph
    current_question_index: int = Field(default=0, ge=0)
    last_was_follow_up: bool = Field(default=False)

    # option to enable humanizer
    enable_humanizer: bool = True

    awaiting_user_input: bool = False

    model_config = {
        "arbitrary_types_allowed": False,
        "extra": "forbid",
    }

    # ---------------------------------------------------------
    # Derived scoring (read-only)
    # ---------------------------------------------------------

    total_score: float = Field(default=0.0, ge=0.0, le=100.0)
    @property
    def computed_total_score(self) -> float:
        if not self.evaluations:
            return 0.0
        average = sum(ev.score for ev in self.evaluations) / len(self.evaluations)

        # defensive bounding
        return max(0.0, min(100.0, average))

    # ---------------------------------------------------------
    # Progress consistency
    # ---------------------------------------------------------

    @model_validator(mode="after")
    def validate_progress_consistency(self) -> "InterviewState":

        if self.progress == InterviewProgress.COMPLETED:
            if not self.evaluations:
                raise ValueError("Cannot complete interview without evaluations")

        if self.progress == InterviewProgress.IN_PROGRESS:
            if not self.questions:
                raise ValueError("Cannot be in progress without questions")

        return self
