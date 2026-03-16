# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState

from app.graph.nodes.question_node import build_question_node
from app.graph.nodes.answer_handler_node import build_answer_handler_node
from app.graph.nodes.complete_node import complete_node

from app.graph.routing.interview_router import route_next_step


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------

    graph.add_node(
        "question",
        build_question_node(llm),
    )

    graph.add_node(
        "answer_handler",
        build_answer_handler_node(llm),
    )

    graph.add_node(
        "complete",
        complete_node,
    )

    # ---------------------------------------------------------
    # Entry
    # ---------------------------------------------------------

    graph.set_entry_point("question")

    # ---------------------------------------------------------
    # Flow
    # ---------------------------------------------------------
    # IMPORTANT:
    # We do NOT automatically go from question → answer_handler.
    # The UI explicitly invokes the graph when the user submits an answer.

    graph.add_conditional_edges(
        "answer_handler",
        route_next_step,
        {
            "complete": "complete",
            "__end__": END,
        },
    )

    graph.add_edge("complete", END)

    return graph.compile()
