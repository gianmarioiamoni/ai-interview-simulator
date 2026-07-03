# domain/contracts/interview_state/base.py

from pydantic import BaseModel, Field, field_validator
from typing import Optional, Dict, List, FrozenSet

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
from domain.contracts.interview.interview_context_profile import InterviewContextProfile
from app.settings.constants import MAX_FOLLOW_UPS_PER_INTERVIEW
from domain.contracts.interview_state.last_question_context import LastQuestionContext
from domain.events.interview_event import InterviewEvent
from domain.contracts.reasoning.interview_memory import InterviewMemory
from domain.contracts.reasoning.reasoner_decision import ReasonerDecision

# V1.2 TCP imports (PAT-04 — Temporary Construction Placeholders)
# These types are imported lazily at class level; they do not introduce
# circular dependencies (verified: all three modules have no path back to
# interview_state).
from domain.contracts.observation.observation_store import ObservationStore
from domain.contracts.reasoning.candidate_profile import CandidateProfile as _CandidateProfileV12
from domain.contracts.session_history.session_history import SessionHistory


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

    report_output: str | None = None
    interview_evaluation: Optional[InterviewEvaluation] = None
    interview_metrics: InterviewMetrics | None = None
    interview_cost_metrics: InterviewCostMetrics | None = None

    chat_history: list[str] = Field(default_factory=list)

    results_by_question: dict[str, QuestionResult] = Field(default_factory=dict)
    dimension_signals: Dict[PerformanceDimensionType, float] = Field(
        default_factory=dict
    )

    current_question_index: int = 0

    awaiting_user_input: bool = False

    memory_context: InterviewMemoryContext = Field(default_factory=InterviewMemoryContext)

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

    # --- Interview Reasoner (V1.1 M2, ADR-032) ---
    # Single-writer: InterviewReasoner only.
    # Supersedes interview_memory_context (deprecated below).
    interview_memory: InterviewMemory = Field(default_factory=InterviewMemory)

    # Advisory output of the last ReasonerNode cycle.
    # Transient: meaningful only for the immediately following nodes.
    # Reset to None at the start of each new question cycle.
    current_reasoning_decision: ReasonerDecision | None = None

    # ----------------------------------------------------------------
    # V1.2 TCP fields (PAT-04 — Temporary Construction Placeholders)
    # RIB-01 MIG-01: additive, nullable, no-op until activated by MIG-02/03/04.
    # No V1.1 node reads or writes these fields.
    # ----------------------------------------------------------------

    # Populated by reasoner_node Phase C (MIG-02).
    # Sole writer: ObservationExtractor (via KnowledgePipeline).
    # Sole reader: KnowledgePipeline, session_close_node.
    # Lifetime: session-scoped; None until first ObservationExtractor cycle.
    observation_store: ObservationStore | None = Field(
        default=None,
        description=(
            "[V1.2 TCP] Session-scoped ObservationStore. "
            "Populated by reasoner_node Phase C (MIG-02). "
            "None until activated. No V1.1 node reads this field."
        ),
    )

    # Populated by reasoner_node Phase D (MIG-03) via KnowledgePipeline.
    # Sole writer: CandidateProfileBuilder (via FeatureEngine / KnowledgePipeline).
    # Sole reader: NarrativeGenerator, CoachingEngine, SessionClosePipeline.
    # Lifetime: session-scoped; updated each reasoning cycle (MIG-03+).
    # Type: same CandidateProfile contract as V1.1; populated via ProfileFeature[]
    #       path (FeatureEngine → CandidateProfileBuilder) rather than
    #       CandidateProfileEngine (dimension_scores) path.
    candidate_profile_v2: _CandidateProfileV12 | None = Field(
        default=None,
        description=(
            "[V1.2 TCP] CandidateProfile produced by FeatureEngine path. "
            "Populated by KnowledgePipeline in reasoner_node Phase D (MIG-03). "
            "None until activated. No V1.1 node reads this field."
        ),
    )

    # Populated by session_close_node (MIG-04) via SessionClosePipeline.
    # Sole writer: SessionHistoryBuilder (via SessionClosePipeline).
    # Sole reader: report_node (MIG-05).
    # Lifetime: written once at session completion; never mutated.
    session_history: SessionHistory | None = Field(
        default=None,
        description=(
            "[V1.2 TCP] Write-once SessionHistory. "
            "Populated by session_close_node (MIG-04). "
            "None until session completion. No V1.1 node reads this field."
        ),
    )

    # DEPRECATED (V1.1 M2) — use interview_memory instead.
    # Still populated by AdaptiveInterviewMemoryBridge for backward compat.
    # Will be removed in M3 (ADR-032).

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
        # Required for ObservationStore (ABC) and SessionHistory TCP fields.
        # Does not loosen any other validation constraint.
        "arbitrary_types_allowed": True,
    }
