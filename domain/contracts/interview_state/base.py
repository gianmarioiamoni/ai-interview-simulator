# domain/contracts/interview_state/base.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List

from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.question.question import Question
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.interview.interview_progress import InterviewProgress
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_evaluation import InterviewEvaluation
from domain.contracts.interview.interview_cost_metrics import InterviewCostMetrics
from domain.contracts.interview.interview_metrics import InterviewMetrics
from domain.contracts.user.role import Role
from domain.contracts.shared.action_type import ActionType
from domain.contracts.interview.interview_memory_context import InterviewMemoryContext

from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)

from app.ui.constants.loader_steps import LoaderStep
from app.contracts.feedback_bundle import FeedbackBundle


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
    interview_metrics: InterviewMetrics | None = None
    interview_cost_metrics: InterviewCostMetrics | None = None

    chat_history: list[str] = Field(default_factory=list)

    results_by_question: dict[str, QuestionResult] = Field(default_factory=dict)
    dimension_signals: Dict[PerformanceDimensionType, float] = Field(
        default_factory=dict
    )

    current_question_index: int = 0
    current_question: Optional[object] = None
    allowed_actions: List = []

    awaiting_user_input: bool = False

    memory_context: InterviewMemoryContext = Field(default_factory=InterviewMemoryContext)

    retrieval_memory: InterviewRetrievalMemory = Field(
        default_factory=InterviewRetrievalMemory,
    )

    planned_areas: list[str] = Field(default_factory=list)

    adaptive_interview_enabled: bool = False

    seniority_level: str = "mid"
    interview_length: int = 20

    # Humanizer (bound aligned with HumanizerPolicyEngine.MAX_FOLLOW_UPS)
    enable_humanizer: bool = True
    follow_up_count: int = Field(default=0, ge=0, le=2)
    last_humanizer_follow_up: bool = False

    events: list = Field(default_factory=list)

    last_feedback_bundle: Optional[FeedbackBundle] = None

    allowed_actions: list[ActionType] = Field(default_factory=list)

    is_completed: bool = False

    is_processing: bool = False

    current_step: Optional[LoaderStep] = None
    current_progress: int = 0

    intent: ActionType | None = None

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
