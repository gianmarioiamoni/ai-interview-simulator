# app/graph/execution_graph.py

# Execution graph
#
# - Minimal LangGraph for answer execution
# - Used in submit flow (EvaluateAnswerUseCase)
# - Orchestrates only ExecutionNode (STEP 1 migration)

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState

from app.graph.nodes.execution_node import ExecutionNode
from app.graph.nodes.evaluation_node import EvaluationNode
from app.graph.nodes.hint_node import HintNode

from services.execution_engine import ExecutionEngine
from services.ai_hint_engine.ai_hint_service import AIHintService


def build_execution_graph(
    execution_engine=None,
    hint_service=None,
):

    execution_engine = execution_engine or ExecutionEngine()
    hint_service = hint_service or AIHintService()

    graph = StateGraph(InterviewState)

    execution_node = ExecutionNode(execution_engine)
    evaluation_node = EvaluationNode()
    hint_node = HintNode(hint_service)

    graph.add_node("execution", execution_node)
    graph.add_node("evaluation", evaluation_node)
    graph.add_node("hint", hint_node)

    graph.set_entry_point("execution")

    graph.add_edge("execution", "evaluation")
    graph.add_edge("evaluation", "hint")
    graph.add_edge("hint", END)

    return graph.compile()
