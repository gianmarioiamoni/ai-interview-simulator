# app/graph/nodes/adaptive_navigation_node.py

from typing import Callable

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import Question
from domain.contracts.question.question_result import QuestionResult
from domain.contracts.question.sql_domain import SqlDomain
from domain.contracts.shared.action_type import ActionType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.business_context import BusinessContext

from app.ui.constants.loader_steps import LoaderStep
from app.graph.nodes.navigation_node import _build_last_question_context
from services.question_corpus.contracts.interview_retrieval_memory import (
    InterviewRetrievalMemory,
)
from services.question_corpus.retrieval.interview_memory_updater import (
    InterviewMemoryUpdater,
)
from services.question_intelligence.lazy_adaptive_interview_service import (
    LazyAdaptiveInterviewService,
)
from services.question_intelligence.question_difficulty_mapper import (
    question_difficulty_to_corpus_int,
)
from services.question_intelligence.session_variety_memory import (
    SessionVarietyMemoryHelper,
)
from app.core.logger import get_logger

logger = get_logger(__name__)


def _update_retrieval_memory(
    memory: InterviewRetrievalMemory,
    question: Question,
    result: QuestionResult | None,
    memory_updater: InterviewMemoryUpdater,
    variety_memory: SessionVarietyMemoryHelper,
) -> InterviewRetrievalMemory:
    """Update retrieval memory from question result (was AdaptiveInterviewMemoryBridge)."""

    evaluation_score: float | None = None

    if result is not None:
        if result.evaluation is not None:
            evaluation_score = result.evaluation.score / 100.0
        elif result.execution is not None:
            execution = result.execution
            if execution.total_tests and execution.total_tests > 0:
                evaluation_score = execution.passed_tests / execution.total_tests
            else:
                evaluation_score = 1.0 if execution.success else 0.0

    if evaluation_score is not None:
        return memory_updater.update_from_question_evaluation(
            memory=memory,
            question=question,
            evaluation_score=evaluation_score,
        )

    if question.id in memory.asked_question_ids:
        return memory

    difficulty_int = question_difficulty_to_corpus_int(question.difficulty)
    updated = memory.model_copy(
        update={
            "asked_question_ids": [*memory.asked_question_ids, question.id],
            "covered_domains": list(
                set([
                    *memory.covered_domains,
                    SqlDomain(question.area.value)
                    if question.area.value in SqlDomain._value2member_map_
                    else SqlDomain.TECHNICAL_DATABASE,
                ]),
            ),
            "difficulty_history": [*memory.difficulty_history, difficulty_int],
        },
    )
    return variety_memory.record_question(memory=updated, question=question)


class AdaptiveNavigationNode:

    def __init__(
        self,
        lazy_service: LazyAdaptiveInterviewService | None = None,
        question_enricher: Callable[[Question], Question] | None = None,
        seniority_level: SeniorityLevel | None = None,
    ) -> None:

        self._lazy_service = lazy_service
        self._memory_updater = InterviewMemoryUpdater()
        self._variety_memory = SessionVarietyMemoryHelper()
        self._question_enricher = question_enricher
        self._seniority_level = seniority_level

    def __call__(self, state: InterviewState) -> InterviewState:

        action = state.intent
        questions = state.questions or []
        current_index = state.current_question_index or 0

        if not questions:
            return state

        last_index = len(questions) - 1

        if action == ActionType.RETRY:

            question = state.current_question
            new_state = state

            if question:
                new_state = new_state.clear_result_for_question(question.id)

            return new_state.model_copy(
                update={
                    "awaiting_user_input": True,
                    "last_feedback_bundle": None,
                    "allowed_actions": [],
                    "intent": None,
                }
            )

        if action == ActionType.NEXT:

            snapshot = _build_last_question_context(state)
            retrieval_memory = state.retrieval_memory
            current_question = state.current_question

            if current_question is not None:
                result = state.results_by_question.get(current_question.id)
                retrieval_memory = _update_retrieval_memory(
                    memory=retrieval_memory,
                    question=current_question,
                    result=result,
                    memory_updater=self._memory_updater,
                    variety_memory=self._variety_memory,
                )

            if (
                state.adaptive_interview_enabled
                and state.planned_areas
                and self._lazy_service is not None
                and current_index >= last_index
                and len(questions) < len(state.planned_areas)
            ):
                level = (
                    self._seniority_level
                    if self._seniority_level is not None
                    else SeniorityLevel(state.seniority_level)
                )
                job_description = (
                    state.context_profile.job_description
                    if state.context_profile is not None
                    else None
                )
                company_description = (
                    state.context_profile.company_description
                    if state.context_profile is not None
                    else None
                )
                business_context = (
                    state.context_profile.business_context
                    if state.context_profile is not None
                    else BusinessContext.GENERIC
                )
                try:
                    new_question, retrieval_memory = self._lazy_service.generate_next_question(
                        role=state.role.type,
                        level=level,
                        interview_type=state.interview_type,
                        planned_areas=state.planned_areas,
                        generated_count=len(questions),
                        memory=retrieval_memory,
                        job_description=job_description,
                        company_description=company_description,
                        business_context=business_context,
                    )
                except Exception as exc:
                    logger.error(
                        "Adaptive question generation failed (count=%s, areas=%s): %s",
                        len(questions),
                        len(state.planned_areas),
                        exc,
                    )
                    # Fallback: advance within already-generated questions if possible,
                    # otherwise stay on current question so the candidate can generate report.
                    if current_index < last_index:
                        return state.model_copy(
                            update={
                                "current_question_index": current_index + 1,
                                "last_question_context": snapshot,
                                "question_display_text": None,
                                "retrieval_memory": retrieval_memory,
                                "awaiting_user_input": True,
                                "last_feedback_bundle": None,
                                "allowed_actions": [],
                                "intent": None,
                            }
                        )
                    return state.model_copy(
                        update={
                            "retrieval_memory": retrieval_memory,
                            "awaiting_user_input": True,
                            "intent": None,
                        }
                    )

                if self._question_enricher is not None:
                    new_question = self._question_enricher(new_question)

                updated_questions = [*questions, new_question]

                return state.model_copy(
                    update={
                        "questions": updated_questions,
                        "current_question_index": current_index + 1,
                        "last_question_context": snapshot,
                        "question_display_text": None,
                        "retrieval_memory": retrieval_memory,
                        "awaiting_user_input": True,
                        "last_feedback_bundle": None,
                        "allowed_actions": [],
                        "intent": None,
                    }
                )

            if current_index < last_index:
                return state.model_copy(
                    update={
                        "current_question_index": current_index + 1,
                        "last_question_context": snapshot,
                        "question_display_text": None,
                        "retrieval_memory": retrieval_memory,
                        "awaiting_user_input": True,
                        "last_feedback_bundle": None,
                        "allowed_actions": [],
                        "intent": None,
                    }
                )

            return state.model_copy(
                update={
                    "retrieval_memory": retrieval_memory,
                    "awaiting_user_input": True,
                    "intent": None,
                }
            )

        if action == ActionType.GENERATE_REPORT:

            return state.model_copy(
                update={
                    "awaiting_user_input": False,
                    "intent": None,
                    "current_step": LoaderStep.GENERATING_REPORT,
                }
            )

        return state
