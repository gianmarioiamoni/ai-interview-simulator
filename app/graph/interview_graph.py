# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END
from domain.contracts.interview_state import InterviewState

from app.graph.nodes.ask_question_node import ask_question_node
from app.graph.nodes.execution_node import execution_node
from app.graph.nodes.scoring_node import scoring_node
from app.graph.nodes.termination_node import termination_node
from app.graph.nodes.evaluate_node import build_evaluate_node
from app.graph.nodes.progression_node import build_progression_node
from app.graph.nodes.humanizer_node import build_humanizer_node


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    evaluate_node = build_evaluate_node(llm)
    humanizer_node = build_humanizer_node(llm)
    progression_node = build_progression_node()

    graph.add_node("ask_question", ask_question_node)
    graph.add_node("humanizer", humanizer_node)
    graph.add_node("execution", execution_node)
    graph.add_node("evaluate", evaluate_node)
    graph.add_node("scoring", scoring_node)
    graph.add_node("progression", progression_node)
    graph.add_node("termination", termination_node)

    graph.set_entry_point("ask_question")

    graph.add_edge("ask_question", "humanizer")

    graph.add_conditional_edges(
        "humanizer",
        lambda state: (
            "execution"
            if state.current_question
            and state.current_question.type.value in ["coding", "database"]
            else "evaluate"
        ),
    )

    graph.add_edge("execution", "scoring")
    graph.add_edge("evaluate", "scoring")

    graph.add_edge("scoring", "progression")
    graph.add_edge("progression", "termination")

    graph.add_conditional_edges(
        "termination",
        lambda state: (
            END
            if state.awaiting_user_input
            else (END if state.progress.name == "COMPLETED" else "ask_question")
        ),
    )

    return graph.compile()
