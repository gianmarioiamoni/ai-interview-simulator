# app/graph/nodes/navigation_node.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.shared.action_type import ActionType

from app.ui.constants.loader_steps import LoaderStep

from typing import Callable

from domain.contracts.question.question import Question

from services.question_intelligence.lazy_adaptive_interview_service import (
    LazyAdaptiveInterviewService,
)

_default_navigation_node: "AdaptiveNavigationNode | None" = None


def configure_navigation_node(
    lazy_service: LazyAdaptiveInterviewService | None = None,
    question_enricher: Callable[[Question], Question] | None = None,
) -> None:

    global _default_navigation_node

    from app.graph.nodes.adaptive_navigation_node import AdaptiveNavigationNode

    _default_navigation_node = AdaptiveNavigationNode(
        lazy_service=lazy_service,
        question_enricher=question_enricher,
    )


def navigation_node(state: InterviewState) -> InterviewState:

    if _default_navigation_node is not None:
        return _default_navigation_node(state)

    return _legacy_navigation_node(state)


def _legacy_navigation_node(state: InterviewState) -> InterviewState:

    action = state.intent
    questions = state.questions or []
    current_index = state.current_question_index or 0

    if not questions:
        return state

    last_index = len(questions) - 1

    # ---------------------------------------------------------
    # RETRY
    # ---------------------------------------------------------
    if action == ActionType.RETRY:

        q = state.current_question
        new_state = state

        if q:
            new_state = new_state.clear_result_for_question(q.id)

        return new_state.model_copy(
            update={
                "awaiting_user_input": True,
                "last_feedback_bundle": None,
                "allowed_actions": [],
                "intent": None,  
            }
        )

    # ---------------------------------------------------------
    # NEXT
    # ---------------------------------------------------------
    if action == ActionType.NEXT:

        if current_index < last_index:
            return state.model_copy(
                update={
                    "current_question_index": current_index + 1,
                    "awaiting_user_input": True,
                    "last_feedback_bundle": None,
                    "allowed_actions": [],
                    "intent": None,  
                }
            )

        # LAST QUESTION → stay here
        return state.model_copy(
            update={
                "awaiting_user_input": True,
                "intent": None,  
            }
        )

    # ---------------------------------------------------------
    # GENERATE REPORT
    # ---------------------------------------------------------
    if action == ActionType.GENERATE_REPORT:

        return state.model_copy(
            update={
                "awaiting_user_input": False,
                "intent": None,  
                "current_step": LoaderStep.GENERATING_REPORT,
            }
        )

    return state
