# app/graph/nodes/adaptive_navigation_node.py

from typing import Callable

from domain.contracts.interview_state import InterviewState
from domain.contracts.question.question import Question
from domain.contracts.shared.action_type import ActionType
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.interview.business_context import BusinessContext

from app.ui.constants.loader_steps import LoaderStep
from services.question_intelligence.adaptive_interview_memory_bridge import (
    AdaptiveInterviewMemoryBridge,
)
from services.question_intelligence.lazy_adaptive_interview_service import (
    LazyAdaptiveInterviewService,
)


class AdaptiveNavigationNode:

    def __init__(
        self,
        lazy_service: LazyAdaptiveInterviewService | None = None,
        memory_bridge: AdaptiveInterviewMemoryBridge | None = None,
        question_enricher: Callable[[Question], Question] | None = None,
        seniority_level: SeniorityLevel | None = None,
    ) -> None:

        self._lazy_service = lazy_service
        self._memory_bridge = (
            memory_bridge
            if memory_bridge is not None
            else AdaptiveInterviewMemoryBridge()
        )
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

            retrieval_memory = state.retrieval_memory
            current_question = state.current_question

            if current_question is not None:
                result = state.results_by_question.get(current_question.id)
                retrieval_memory = self._memory_bridge.update_from_question_result(
                    memory=retrieval_memory,
                    question=current_question,
                    result=result,
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

                if self._question_enricher is not None:
                    new_question = self._question_enricher(new_question)

                updated_questions = [*questions, new_question]

                return state.model_copy(
                    update={
                        "questions": updated_questions,
                        "current_question_index": current_index + 1,
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
