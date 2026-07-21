# domain/contracts/interview_state/base.py

from pydantic import BaseModel, Field
from typing import Optional, Dict, List, FrozenSet

from domain.contracts.shared.performance_dimension_type import PerformanceDimensionType
from domain.contracts.question.question import Question
from domain.contracts.interview.answer import Answer
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.interview.interview_type import InterviewType
from domain.contracts.interview.interview_cost_metrics import InterviewCostMetrics
from domain.contracts.interview.interview_metrics import InterviewMetrics
from domain.contracts.user.role import Role
from domain.contracts.shared.action_type import ActionType
from domain.contracts.question.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from domain.contracts.interview.loader_step import LoaderStep
from domain.contracts.feedback.feedback import FeedbackBundle
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from domain.contracts.interview.follow_up_limits import MAX_FOLLOW_UPS_PER_INTERVIEW
from domain.contracts.interview_state.last_question_context import LastQuestionContext
from domain.events.interview_event import InterviewEvent
from domain.contracts.reasoning.interview_memory import InterviewMemory

from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.reasoning.candidate_profile import CandidateProfile as _CandidateProfileV12
from domain.contracts.report.scoring_narrative import ScoringNarrative
from domain.contracts.report.scoring_snapshot import ScoringSnapshot
from domain.contracts.session_history.session_history import SessionHistory
from domain.contracts.report.report import Report


class InterviewStateBase(BaseModel):

    interview_id: str
    role: Role
    company: str
    language: str = "en"
    interview_type: InterviewType = InterviewType.TECHNICAL

    questions: list[Question] = Field(default_factory=list)
    asked_question_ids: list[str] = Field(default_factory=list)
    answers: list[Answer] = Field(default_factory=list)

    interview_metrics: InterviewMetrics | None = None
    interview_cost_metrics: InterviewCostMetrics | None = None

    # Phase 7A (ADR-033): new scoring artifacts — sole writer: EvaluationAggregateNode.
    scoring_snapshot: ScoringSnapshot | None = None
    scoring_narrative: ScoringNarrative | None = None

    chat_history: list[str] = Field(default_factory=list)

    results_by_question: dict[str, QuestionResult] = Field(default_factory=dict)
    dimension_signals: Dict[PerformanceDimensionType, float] = Field(
        default_factory=dict
    )

    current_question_index: int = 0

    awaiting_user_input: bool = False

    retrieval_memory: InterviewRetrievalMemory = Field(
        default_factory=InterviewRetrievalMemory,
    )

    planned_areas: list[str] = Field(default_factory=list)

    adaptive_interview_enabled: bool = False

    seniority_level: str = "mid"
    interview_length: int = 20

    context_profile: InterviewContextProfile = Field(
        default_factory=InterviewContextProfile,
    )

    enable_humanizer: bool = True
    follow_up_count: int = Field(default=0, ge=0, le=MAX_FOLLOW_UPS_PER_INTERVIEW)
    last_humanizer_follow_up: bool = False
    last_question_context: LastQuestionContext | None = None
    question_display_text: str | None = None

    # Populated once at session start by FollowUpSelector.
    # Contains the indices of questions eligible to trigger a follow-up.
    # Never modified after initial population.
    follow_up_eligible_indices: FrozenSet[int] = Field(default_factory=frozenset)

    events: list[InterviewEvent] = Field(default_factory=list)

    last_feedback_bundle: Optional[FeedbackBundle] = None

    # Single-writer: InterviewReasoner only (ADR-032).
    interview_memory: InterviewMemory = Field(default_factory=InterviewMemory)

    # ----------------------------------------------------------------
    # V1.2 fields — session-scoped, nullable until each pipeline stage runs.
    # ----------------------------------------------------------------

    # Set once at session creation. Immutable for session lifetime.
    # Sole writer: InterviewStateFactoryMixin.create_initial / create_empty.
    # Consumed by: KnowledgePipelineContext, SessionHistory.
    candidate_identity_id: str | None = Field(
        default=None,
        description=(
            "Stable candidate identity for pipeline context. "
            "Set once at session start; immutable for session lifetime. "
            "Consumed by KnowledgePipelineContext. "
            "None only in states predating V1.2."
        ),
    )

    # Sole writer: ObservationExtractor (via reasoner_node).
    # Sole reader: KnowledgePipeline, session_close_node.
    # Lifetime: session-scoped; None until first reasoner cycle.
    observation_store: ObservationStore | None = Field(
        default=None,
        description=(
            "Session-scoped ObservationStore. "
            "Populated by reasoner_node. None until activated."
        ),
    )

    # Sole writer: CandidateProfileBuilder (via FeatureEngine / KnowledgePipeline).
    # Sole reader: NarrativeGenerator, CoachingEngine, SessionClosePipeline.
    # Lifetime: session-scoped; updated each reasoning cycle.
    candidate_profile_v2: _CandidateProfileV12 | None = Field(
        default=None,
        description=(
            "CandidateProfile produced by FeatureEngine path. "
            "Populated by KnowledgePipeline in reasoner_node. None until activated."
        ),
    )

    # Sole writer: SessionHistoryBuilder (via session_close_node).
    # Sole reader: report_node.
    # Lifetime: written once at session completion; never mutated.
    session_history: SessionHistory | None = Field(
        default=None,
        description=(
            "Write-once SessionHistory. "
            "Populated by session_close_node. None until session completion."
        ),
    )

    # Sole writer: ReportBuilder (via report_node). Write-once.
    # Sole reader: UI layer / export pipeline.
    # Lifetime: written once at report generation; never mutated.
    report: Report | None = Field(
        default=None,
        description=(
            "Immutable Report assembled by report_node. "
            "Populated from SessionHistory. None until report generation."
        ),
    )

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
        # Required for ObservationStore (ABC) and SessionHistory fields.
        "arbitrary_types_allowed": True,
    }
