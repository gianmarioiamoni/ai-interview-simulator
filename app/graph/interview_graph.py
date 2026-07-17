# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState
from app.core.logger import get_logger

logger = get_logger(__name__)
from domain.contracts.question.question import QuestionType
from domain.contracts.shared.action_type import ActionType

from app.graph.nodes.execution_node import ExecutionNode
from app.graph.nodes.evaluation_node import EvaluationNode
from app.graph.nodes.feedback_node import FeedbackNode
from app.graph.nodes.hint_node import HintNode
from app.graph.nodes.decision_node import DecisionNode
from app.graph.nodes.written_evaluation_node import WrittenEvaluationNode
from app.graph.nodes.navigation_node import navigation_node
from app.graph.nodes.completion_node import completion_node
from app.graph.nodes.report_node import report_node
from app.graph.nodes.evaluation_aggregate_node import EvaluationAggregateNode
from app.graph.nodes.start_processing_node import start_processing_node
from app.graph.nodes.question_node import build_question_node
from app.graph.nodes.reasoner_node import reasoner_node
from app.graph.nodes.session_close_node import session_close_node
from app.graph.nodes.longitudinal_update_node import LongitudinalUpdateNode

from services.execution_engine import ExecutionEngine
from services.ai_hint_engine.ai_hint_service import AIHintService
from services.interview_evaluation_service import InterviewEvaluationService

from app.ports.llm_port import LLMPort
from domain.contracts.longitudinal.longitudinal_profile_repository import (
    LongitudinalProfileRepository,
)
from infrastructure.observability.graph_node_logging import instrument_graph_node


# ---------------------------------------------------------
# ROUTING: entry decision
# ---------------------------------------------------------


def route_entry(state: InterviewState) -> str:

    # navigation ONLY if user explicitly triggered it
    if state.intent in [
        ActionType.RETRY,
        ActionType.NEXT,
        ActionType.GENERATE_REPORT,
    ]:
        return "navigation"

    return "router"


# ---------------------------------------------------------
# ROUTING: question type
# ---------------------------------------------------------


def route_by_question_type(state: InterviewState) -> str:

    question = state.current_question

    if question is None:
        return "execution"

    if question.type == QuestionType.WRITTEN:
        return "written"

    return "execution"


# ---------------------------------------------------------
# ROUTER NODE
# ---------------------------------------------------------


def router_node(state: InterviewState) -> InterviewState:
    return state


# ---------------------------------------------------------
# GRAPH BUILDER
# ---------------------------------------------------------


def build_interview_graph(
    llm: LLMPort,
    hint_service: AIHintService | None = None,
    longitudinal_repository: LongitudinalProfileRepository | None = None,
):

    graph = StateGraph(InterviewState)

    # -----------------------------------------------------
    # Dependencies
    # -----------------------------------------------------

    evaluation_service = InterviewEvaluationService(llm)
    execution_engine = ExecutionEngine()
    hint_service = hint_service or AIHintService(llm)

    if longitudinal_repository is None:
        from pathlib import Path
        from infrastructure.longitudinal.longitudinal_profile_repository_impl import (
            JsonFileLongitudinalProfileRepository,
        )
        longitudinal_repository = JsonFileLongitudinalProfileRepository(
            storage_dir=Path("data/longitudinal")
        )

    longitudinal_update = LongitudinalUpdateNode(repository=longitudinal_repository)

    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------

    # Batch A (C5): core interview cycle — structured logging via sole helper.
    # Batch B (C6): session_close, report, longitudinal_update, entry.
    graph.add_node("router", instrument_graph_node("router", router_node))
    graph.add_node("navigation", instrument_graph_node("navigation", navigation_node))
    graph.add_node("question", instrument_graph_node("question", build_question_node(llm)))
    graph.add_node(
        "execution", instrument_graph_node("execution", ExecutionNode(execution_engine))
    )
    graph.add_node("evaluation", instrument_graph_node("evaluation", EvaluationNode()))
    graph.add_node(
        "evaluation_aggregate",
        instrument_graph_node(
            "evaluation_aggregate", EvaluationAggregateNode(evaluation_service)
        ),
    )
    graph.add_node("feedback", instrument_graph_node("feedback", FeedbackNode(llm)))
    graph.add_node("reasoner", instrument_graph_node("reasoner", reasoner_node))
    graph.add_node("hint", instrument_graph_node("hint", HintNode(hint_service)))
    graph.add_node("decision", instrument_graph_node("decision", DecisionNode()))
    graph.add_node(
        "written", instrument_graph_node("written", WrittenEvaluationNode(llm))
    )
    graph.add_node("completion", instrument_graph_node("completion", completion_node))
    graph.add_node("session_close", session_close_node)
    graph.add_node("report", report_node)
    graph.add_node("longitudinal_update", longitudinal_update)
    graph.add_node(
        "start_processing",
        instrument_graph_node("start_processing", start_processing_node),
    )

    # -----------------------------------------------------
    # Entry
    # -----------------------------------------------------

    graph.set_entry_point("entry")
    graph.add_node("entry", lambda state: state)

    graph.add_conditional_edges(
        "entry",
        route_entry,
        {
            "navigation": "start_processing",
            "router": "router",
        },
    )

    # -----------------------------------------------------
    # Question routing
    # -----------------------------------------------------

    graph.add_conditional_edges(
        "router",
        route_by_question_type,
        {
            "execution": "execution",
            "written": "written",
        },
    )

    # -----------------------------------------------------
    # Execution path
    # -----------------------------------------------------

    graph.add_edge("execution", "evaluation")
    graph.add_edge("evaluation", "hint")
    graph.add_edge("hint", "feedback")

    # -----------------------------------------------------
    # Written path
    # -----------------------------------------------------

    graph.add_edge("written", "feedback")

    # -----------------------------------------------------
    # Shared tail
    # -----------------------------------------------------

    graph.add_edge("feedback", "reasoner")
    graph.add_edge("reasoner", "decision")

    def route_after_decision(state: InterviewState) -> str:

        # STOP → FEEDBACK phase
        if state.awaiting_user_input:
            return END

        return "navigation"

    graph.add_conditional_edges(
        "decision",
        route_after_decision,
        {
            "navigation": "navigation",
            END: END,
        },
    )

    # -----------------------------------------------------
    # Navigation flow
    # -----------------------------------------------------

    graph.add_edge("start_processing", "navigation")
    
    graph.add_edge("navigation", "question")
    graph.add_edge("question", "completion")
    graph.add_edge("completion", "evaluation_aggregate")

    def route_after_completion(state: InterviewState) -> str:
        logger.debug("route_after_completion: is_completed=%s", state.is_completed)

        if state.is_completed:
            return "session_close"

        return END

    graph.add_conditional_edges(
        "evaluation_aggregate",
        route_after_completion,
        {
            "session_close": "session_close",
            END: END,
        },
    )

    graph.add_edge("session_close", "report")
    graph.add_edge("report", "longitudinal_update")
    graph.add_edge("longitudinal_update", END)

    return graph.compile()
