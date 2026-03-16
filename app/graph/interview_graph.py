# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState
from app.graph.nodes.question_node import build_question_node


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------

    graph.add_node(
        "question",
        build_question_node(llm),
    )

    # ---------------------------------------------------------
    # Entry
    # ---------------------------------------------------------

    graph.set_entry_point("question")

    # ---------------------------------------------------------
    # Flow
    # ---------------------------------------------------------

    graph.add_edge("question", END)

    return graph.compile()
