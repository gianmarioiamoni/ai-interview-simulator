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
from services.execution_engine import ExecutionEngine


def build_execution_graph():

    graph = StateGraph(InterviewState)

    execution_engine = ExecutionEngine()
    execution_node = ExecutionNode(execution_engine)
    evaluation_node = EvaluationNode()

    graph.add_node("execution", execution_node)
    graph.add_node("evaluation", evaluation_node)

    graph.set_entry_point("execution")
    
    graph.add_edge("execution", "evaluation")
    graph.add_edge("evaluation", END)

    return graph.compile()
