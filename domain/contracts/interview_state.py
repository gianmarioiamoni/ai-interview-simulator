# domain/contracts/interview_state.py

from __future__ import annotations

from typing import Optional
from pydantic import BaseModel, Field, model_validator

from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.question_evaluation import QuestionEvaluation
from domain.contracts.question_result import QuestionResult
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_type import InterviewType
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.execution_result import ExecutionResult
from domain.contracts.role import Role, RoleType


class InterviewState(BaseModel):

    # ---------------------------------------------------------
    # Basic interview configuration
    # ---------------------------------------------------------

    interview_id: str
    role: Role
    company: str
    language: str = "en"
    interview_type: InterviewType = InterviewType.TECHNICAL

    # ---------------------------------------------------------
    # Progress
    # ---------------------------------------------------------

    progress: InterviewProgress = InterviewProgress.SETUP

    questions: list[Question] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)

    final_evaluation: Optional[InterviewEvaluation] = None

    # ---------------------------------------------------------
    # Conversation
    # ---------------------------------------------------------

    chat_history: list[str] = Field(default_factory=list)

    # ---------------------------------------------------------
    # Results (NEW ARCHITECTURE)
    # ---------------------------------------------------------

    results_by_question: dict[str, QuestionResult] = Field(default_factory=dict)

    # ---------------------------------------------------------
    # Graph state
    # ---------------------------------------------------------

    current_question_index: int = 0

    enable_humanizer: bool = True

    # ---------------------------------------------------------
    # Pydantic config
    # ---------------------------------------------------------

    model_config = {
        "extra": "forbid",
    }

    # =========================================================
    # RESULT MANAGEMENT
    # =========================================================

    def register_evaluation(self, evaluation: QuestionEvaluation):

        qid = evaluation.question_id

        result = self.results_by_question.get(qid)

        if result is None:
            result = QuestionResult(question_id=qid)

        result = result.model_copy(update={"evaluation": evaluation})

        new_map = dict(self.results_by_question)
        new_map[qid] = result

        self.results_by_question = new_map

    # ---------------------------------------------------------

    def register_execution(self, execution: ExecutionResult):

        qid = execution.question_id

        result = self.results_by_question.get(qid)

        if result is None:
            result = QuestionResult(question_id=qid)

        result = result.model_copy(update={"execution": execution})

        new_map = dict(self.results_by_question)
        new_map[qid] = result

        self.results_by_question = new_map

    # ---------------------------------------------------------

    def get_result_for_question(self, question_id: str) -> Optional[QuestionResult]:

        return self.results_by_question.get(question_id)

    # ---------------------------------------------------------

    def get_last_result(self):

        if self.last_answer is None:
            return None

        return self.results_by_question.get(self.last_answer.question_id)

    # ---------------------------------------------------------

    def is_question_processed(self, question):

        result = self.results_by_question.get(question.id)

        if result is None:
            return False

        if question.type.value == "written":
            return result.evaluation is not None

        if question.type.value in ("coding", "database"):
            return result.execution is not None

        return False

    # =========================================================
    # COMPUTED PROPERTIES
    # =========================================================

    @property
    def current_question(self) -> Optional[Question]:

        if not self.questions:
            return None

        if self.current_question_index >= len(self.questions):
            return None

        return self.questions[self.current_question_index]

    # ---------------------------------------------------------

    @property
    def last_answer(self) -> Optional[Answer]:

        if not self.answers:
            return None

        return self.answers[-1]

    # ---------------------------------------------------------

    @property
    def is_last_question(self) -> bool:

        if not self.questions:
            return False

        return self.current_question_index >= len(self.questions) - 1

    # =========================================================
    # DOMAIN METHODS
    # =========================================================

    def register_answer(self, answer: Answer):

        self.answers.append(answer)

    # ---------------------------------------------------------

    def advance_question(self):

        if self.is_last_question:
            self.progress = InterviewProgress.COMPLETED
            return

        self.current_question_index += 1
        self.progress = InterviewProgress.IN_PROGRESS

    # =========================================================
    # VALIDATION
    # =========================================================

    @model_validator(mode="after")
    def validate_progress_consistency(self):

        if self.progress == InterviewProgress.COMPLETED:
            if not self.results_by_question:
                raise ValueError("Cannot complete interview without results")

        return self

    # =========================================================
    # FACTORY
    # =========================================================

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

        return cls(
            interview_id=interview_id,
            role=Role(type=role_type),
            interview_type=interview_type,
            company=company.strip(),
            language=language,
            questions=questions,
            progress=InterviewProgress.SETUP,
        )
