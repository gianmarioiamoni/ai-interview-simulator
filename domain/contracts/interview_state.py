# domain/contracts/interview_state.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, model_validator

from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_type import InterviewType
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.role import Role, RoleType


class InterviewState(BaseModel):

    # ---------------------------------------------------------
    # Basic interview configuration
    # ---------------------------------------------------------

    interview_id: str = Field(..., min_length=1)
    role: Role
    company: str = Field(..., min_length=1)
    language: str = Field(default="en")
    interview_type: InterviewType = Field(default=InterviewType.TECHNICAL)

    # ---------------------------------------------------------
    # Progress tracking
    # ---------------------------------------------------------

    progress: InterviewProgress = Field(default=InterviewProgress.SETUP)

    questions: list[Question] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)
    evaluations: list[QuestionEvaluation] = Field(default_factory=list)

    final_evaluation: Optional[InterviewEvaluation] = None

    # ---------------------------------------------------------
    # Conversational memory (humanizer)
    # ---------------------------------------------------------

    chat_history: list[str] = Field(default_factory=list)

    # ---------------------------------------------------------
    # Execution engines
    # ---------------------------------------------------------

    execution_results: list[ExecutionResult] = Field(default_factory=list)

    # ---------------------------------------------------------
    # LangGraph orchestration
    # ---------------------------------------------------------

    current_question_index: int = Field(default=0, ge=0)

    follow_up_count: int = Field(default=0, ge=0, le=2)
    last_was_follow_up: bool = Field(default=False)

    awaiting_user_input: bool = False

    # ---------------------------------------------------------
    # Feature flags
    # ---------------------------------------------------------

    enable_humanizer: bool = True

    # ---------------------------------------------------------
    # Derived scoring
    # ---------------------------------------------------------

    total_score: float = Field(default=0.0, ge=0.0, le=100.0)

    model_config = {
        "arbitrary_types_allowed": False,
        "extra": "forbid",
    }

    # ---------------------------------------------------------
    # Computed properties
    # ---------------------------------------------------------

    @property
    def computed_total_score(self) -> float:

        if not self.evaluations:
            return 0.0

        avg = sum(ev.score for ev in self.evaluations) / len(self.evaluations)

        return max(0.0, min(100.0, avg))

    # ---------------------------------------------------------

    @property
    def current_question(self) -> Optional[Question]:

        if not self.questions:
            return None

        if self.current_question_index >= len(self.questions):
            return None

        return self.questions[self.current_question_index]

    # ---------------------------------------------------------

    @property
    def current_question_id(self) -> Optional[str]:

        question = self.current_question

        if question is None:
            return None

        return question.id

    # ---------------------------------------------------------

    @property
    def last_answer(self) -> Optional[Answer]:

        if not self.answers:
            return None

        return self.answers[-1]

    # ---------------------------------------------------------

    @property
    def last_evaluation(self) -> Optional[QuestionEvaluation]:

        if not self.evaluations:
            return None

        return self.evaluations[-1]

    # ---------------------------------------------------------

    @property
    def last_execution(self) -> Optional[ExecutionResult]:

        if not self.execution_results:
            return None

        return self.execution_results[-1]

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

    # ---------------------------------------------------------
    # Factory
    # ---------------------------------------------------------

    @classmethod
    def create_initial(
        cls,
        role_type: RoleType,
        interview_type: InterviewType,
        company: str,
        language: str,
        questions: list[Question],
        interview_id: str,
    ) -> "InterviewState":

        if not questions:
            raise ValueError("Cannot create interview without questions")

        return cls(
            interview_id=interview_id,
            role=Role(type=role_type),
            interview_type=interview_type,
            company=company.strip(),
            language=language,
            questions=questions,
            progress=InterviewProgress.SETUP,
        )
