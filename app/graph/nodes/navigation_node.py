# app/graph/nodes/navigation_node.py

from typing import Callable

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_state.last_question_context import LastQuestionContext
from domain.contracts.user.seniority_level import SeniorityLevel
from domain.contracts.question.question import Question

from services.question_intelligence.lazy_adaptive_interview_service import (
    LazyAdaptiveInterviewService,
)

_default_navigation_node: "AdaptiveNavigationNode | None" = None


def configure_navigation_node(
    lazy_service: LazyAdaptiveInterviewService | None = None,
    question_enricher: Callable[[Question], Question] | None = None,
    seniority_level: SeniorityLevel | None = None,
) -> None:

    global _default_navigation_node

    from app.graph.nodes.adaptive_navigation_node import AdaptiveNavigationNode

    _default_navigation_node = AdaptiveNavigationNode(
        lazy_service=lazy_service,
        question_enricher=question_enricher,
        seniority_level=seniority_level,
    )


def navigation_node(state: InterviewState) -> InterviewState:
    """LangGraph navigation node.

    Invariant (PAT-06): configure_navigation_node() MUST be called before the
    first graph invocation.  If it has not been called, startup is broken and
    the graph must not proceed.
    """
    if _default_navigation_node is None:
        raise RuntimeError(
            "navigation_node: AdaptiveNavigationNode has not been configured. "
            "Call configure_navigation_node() during application startup before "
            "invoking the interview graph. "
            "(PAT-06: LangGraph is the sole runtime orchestrator — no fallback path.)"
        )
    return _default_navigation_node(state)


def _build_last_question_context(state: InterviewState) -> LastQuestionContext | None:
    question = state.current_question
    if question is None:
        return None

    answer = state.get_latest_answer_for_question(question.id)
    result = state.results_by_question.get(question.id)

    quality_rank: int | None = None
    if state.last_feedback_bundle is not None:
        quality_rank = state.last_feedback_bundle.overall_quality.rank()
    elif result is not None and result.evaluation is not None:
        score = getattr(result.evaluation, "score", None)
        if score is not None:
            from domain.contracts.feedback.quality import Quality
            quality_rank = min(int(score // 25), Quality.OPTIMAL.rank())

    return LastQuestionContext(
        question_id=question.id,
        question_prompt=question.prompt,
        question_type=question.type,
        question_area=getattr(question, "area", None),
        answer_content=answer.content if answer is not None else None,
        quality_rank=quality_rank,
    )


