# domain/contracts/interview_state/base.py

from pydantic import BaseModel, Field
from typing import Optional, Any

from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.question_result import QuestionResult
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_type import InterviewType
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.role import Role
from domain.contracts.action_type import ActionType


class InterviewStateBase(BaseModel):

    interview_id: str
    role: Role
    company: str
    language: str = "en"
    interview_type: InterviewType = InterviewType.TECHNICAL

    progress: InterviewProgress = InterviewProgress.SETUP

    questions: list[Question] = Field(default_factory=list)
    asked_question_ids: list[str] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)

    report_output: dict | None = None
    interview_evaluation: Optional[InterviewEvaluation] = None

    chat_history: list[str] = Field(default_factory=list)

    results_by_question: dict[str, QuestionResult] = Field(default_factory=dict)

    current_question_index: int = 0

    awaiting_user_input: bool = False

    enable_humanizer: bool = True

    events: list = Field(default_factory=list)

    last_feedback_bundle: Optional[Any] = None

    last_action: Optional[ActionType] = None
    allowed_actions: list[ActionType] = Field(default_factory=list)

    is_completed: bool = False

    def with_current_question(self, question, index):
        return self.model_copy(
            update={
                "current_question_index": index,
                "asked_question_ids": self.asked_question_ids + [question.id],
            }
        )

    model_config = {
        "extra": "forbid",
    }
