# app/graph/interview_graph.py

# Interview graph - progressively extended with execution pipeline

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState
from app.graph.nodes.question_node import build_question_node
from app.graph.nodes.execution_node import ExecutionNode
from services.execution_engine import ExecutionEngine


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------

    graph.add_node(
        "question",
        build_question_node(llm),
    )

    execution_engine = ExecutionEngine()

    graph.add_node(
        "execution",
        ExecutionNode(execution_engine),
    )

    # ---------------------------------------------------------
    # Entry
    # ---------------------------------------------------------

    graph.set_entry_point("question")

    # ---------------------------------------------------------
    # Flow
    # ---------------------------------------------------------

    graph.add_edge("question", "execution")
    graph.add_edge("execution", END)

    return graph.compile()
