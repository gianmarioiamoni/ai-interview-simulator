# domain/contracts/interview_state/base.py

from pydantic import BaseModel, Field
from typing import Optional

from domain.contracts.question import Question
from domain.contracts.answer import Answer
from domain.contracts.question_result import QuestionResult
from domain.contracts.interview_progress import InterviewProgress
from domain.contracts.interview_type import InterviewType
from domain.contracts.interview_evaluation import InterviewEvaluation
from domain.contracts.role import Role

from app.ui.presenters.feedback.feedback_models import FeedbackBundle


class InterviewStateBase(BaseModel):

    interview_id: str
    role: Role
    company: str
    language: str = "en"
    interview_type: InterviewType = InterviewType.TECHNICAL

    progress: InterviewProgress = InterviewProgress.SETUP

    questions: list[Question] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)

    final_evaluation: Optional[InterviewEvaluation] = None

    chat_history: list[str] = Field(default_factory=list)

    results_by_question: dict[str, QuestionResult] = Field(default_factory=dict)

    current_question_index: int = 0

    enable_humanizer: bool = True

    events: list = Field(default_factory=list)

    attempts_by_question: dict[str, int] = Field(default_factory=dict)

    last_feedback_bundle: Optional[FeedbackBundle] = None

    model_config = {
        "extra": "forbid",
    }
