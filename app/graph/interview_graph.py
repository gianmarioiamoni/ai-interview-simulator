# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState
from domain.contracts.question import QuestionType

from app.graph.nodes.execution_node import ExecutionNode
from app.graph.nodes.evaluation_node import EvaluationNode
from app.graph.nodes.feedback_node import FeedbackNode
from app.graph.nodes.hint_node import HintNode
from app.graph.nodes.decision_node import DecisionNode
from app.graph.nodes.written_evaluation_node import WrittenEvaluationNode

from services.execution_engine import ExecutionEngine
from services.ai_hint_engine.ai_hint_service import AIHintService


# ---------------------------------------------------------
# ROUTING FUNCTION (REAL ROUTER)
# ---------------------------------------------------------


def route_by_question_type(state: InterviewState) -> str:

    question = state.current_question

    if question is None:
        return "execution"  # safe fallback

    if question.type == QuestionType.WRITTEN:
        return "written"

    return "execution"


# ---------------------------------------------------------
# ROUTER NODE (PASS-THROUGH)
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

    execution_engine = ExecutionEngine()
    hint_service = hint_service or AIHintService()

    # -----------------------------------------------------
    # Nodes (ordine logico del flusso)
    # -----------------------------------------------------

    graph.add_node("router", router_node)

    graph.add_node("execution", ExecutionNode(execution_engine))
    graph.add_node("evaluation", EvaluationNode())
    graph.add_node("feedback", FeedbackNode())
    graph.add_node("hint", HintNode(hint_service))
    graph.add_node("decision", DecisionNode())

    graph.add_node("written", WrittenEvaluationNode(llm))

    # -----------------------------------------------------
    # Entry point
    # -----------------------------------------------------

    graph.set_entry_point("router")

    # -----------------------------------------------------
    # Routing
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
    # Execution path (coding / db)
    # -----------------------------------------------------

    graph.add_edge("execution", "evaluation")
    graph.add_edge("evaluation", "feedback")

    # -----------------------------------------------------
    # Written path
    # -----------------------------------------------------

    graph.add_edge("written", "feedback")

    # -----------------------------------------------------
    # Shared tail (MERGED)
    # -----------------------------------------------------

    graph.add_edge("feedback", "hint")
    graph.add_edge("hint", "decision")
    graph.add_edge("decision", END)

    # -----------------------------------------------------
    # Compile
    # -----------------------------------------------------

    return graph.compile()
