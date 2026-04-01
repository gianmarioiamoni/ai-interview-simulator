# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType
from domain.contracts.action_type import ActionType

from app.graph.nodes.execution_node import ExecutionNode
from app.graph.nodes.evaluation_node import EvaluationNode
from app.graph.nodes.feedback_node import FeedbackNode
from app.graph.nodes.hint_node import HintNode
from app.graph.nodes.decision_node import DecisionNode
from app.graph.nodes.written_evaluation_node import WrittenEvaluationNode
from app.graph.nodes.navigation_node import navigation_node
from app.graph.nodes.completion_node import completion_node
from app.graph.nodes.report_node import report_node

from services.execution_engine import ExecutionEngine
from services.ai_hint_engine.ai_hint_service import AIHintService
from services.interview_evaluation_service import InterviewEvaluationService


# ---------------------------------------------------------
# ROUTING: entry decision
# ---------------------------------------------------------


def route_entry(state: InterviewState) -> str:

    # navigation ONLY if user explicitly triggered it
    if state.last_action in [ActionType.RETRY, ActionType.NEXT]:
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
    llm,
    hint_service: AIHintService | None = None,
):

    graph = StateGraph(InterviewState)

    # -----------------------------------------------------
    # Dependencies
    # -----------------------------------------------------

    evaluation_service = InterviewEvaluationService(llm)
    execution_engine = ExecutionEngine()
    hint_service = hint_service or AIHintService()

    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------

    graph.add_node("router", router_node)
    graph.add_node("navigation", navigation_node)
    graph.add_node("execution", ExecutionNode(execution_engine))
    graph.add_node("evaluation", EvaluationNode())
    graph.add_node("feedback", FeedbackNode())
    graph.add_node("hint", HintNode(hint_service))
    graph.add_node("decision", DecisionNode())
    graph.add_node("written", WrittenEvaluationNode(llm))
    graph.add_node("completion", completion_node)
    graph.add_node("report", lambda state: report_node(state, evaluation_service))

    # -----------------------------------------------------
    # Entry
    # -----------------------------------------------------

    graph.set_entry_point("entry")
    graph.add_node("entry", lambda state: state)

    graph.add_conditional_edges(
        "entry",
        route_entry,
        {
            "navigation": "navigation",
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
    graph.add_edge("evaluation", "feedback")

    # -----------------------------------------------------
    # Written path
    # -----------------------------------------------------

    graph.add_edge("written", "feedback")

    # -----------------------------------------------------
    # Shared tail
    # -----------------------------------------------------

    graph.add_edge("feedback", "hint")
    graph.add_edge("hint", "decision")

    # 🔥 FIX CRITICO
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

    graph.add_edge("navigation", "completion")

    def route_after_completion(state: InterviewState) -> str:
        print(f"[DEBUG] route_after_completion - is_completed: {state.is_completed}")

        if state.is_completed:
            print("[DEBUG] routing → report")
            return "report"

        print("[DEBUG] routing → END")
        return END

    graph.add_conditional_edges(
        "completion",
        route_after_completion,
        {
            "report": "report",
            END: END,
        },
    )

    graph.add_edge("report", END)

    return graph.compile()
