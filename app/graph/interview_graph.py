# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState

from app.graph.nodes.question_node import build_question_node
from app.graph.nodes.answer_processing_node import answer_processing_node
from app.graph.nodes.evaluation_node import build_evaluation_node
from app.graph.nodes.advance_node import advance_node

from app.graph.routing.interview_router import route_next_step


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    # Nodes
    graph.add_node("question", build_question_node(llm))
    graph.add_node("process_answer", answer_processing_node)
    graph.add_node("evaluate", build_evaluation_node(llm))
    graph.add_node("advance", advance_node)

    # Entry point
    graph.set_entry_point("question")

    # Flow
    graph.add_edge("question", "process_answer")
    graph.add_edge("process_answer", "evaluate")

    graph.add_conditional_edges(
        "evaluate",
        route_next_step,
        {
            "advance": "advance",
            END: END,
        },
    )

    graph.add_edge("advance", "question")

    return graph.compile()
