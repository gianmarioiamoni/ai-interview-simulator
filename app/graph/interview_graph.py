# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END
from domain.contracts.interview_state import InterviewState

from app.graph.nodes.ask_question_node import ask_question_node
from app.graph.nodes.execution_node import execution_node
from app.graph.nodes.scoring_node import scoring_node
from app.graph.nodes.termination_node import termination_node
from app.graph.nodes.evaluator_node import build_evaluator_node
from app.graph.nodes.humanizer_node import build_humanizer_node


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    evaluator_node = build_evaluator_node(llm)
    humanizer_node = build_humanizer_node(llm)

    graph.add_node("ask_question", ask_question_node)
    graph.add_node("humanizer", humanizer_node)
    graph.add_node("execution", execution_node)
    graph.add_node("evaluator", evaluator_node)
    graph.add_node("scoring", scoring_node)
    graph.add_node("termination", termination_node)

    graph.set_entry_point("ask_question")

    graph.add_edge("ask_question", "humanizer")

    graph.add_conditional_edges(
        "humanizer",
        lambda state: (
            "execution"
            if state.current_question_id
            and next(
                q for q in state.questions if q.id == state.current_question_id
            ).type
            in ["coding", "sql"]
            else "evaluator"
        ),
    )

    graph.add_edge("execution", "scoring")
    graph.add_edge("evaluator", "scoring")
    graph.add_edge("scoring", "termination")

    graph.add_conditional_edges(
        "termination",
        lambda state: (
            END
            if state.awaiting_user_input
            else (END if state.progress.name == "COMPLETED" else "ask_question")
        ),
    )

    return graph.compile()
