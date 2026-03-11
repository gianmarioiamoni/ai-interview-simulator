from langgraph.graph import StateGraph
from domain.contracts.interview_state import InterviewState

from app.graph.nodes.question_node import build_question_node
from app.graph.nodes.answer_processing_node import answer_processing_node
from app.graph.nodes.evaluation_node import build_evaluation_node
from app.graph.nodes.advance_node import advance_node


def build_interview_graph(llm):

    graph = StateGraph(InterviewState)

    question_node = build_question_node(llm)
    evaluation_node = build_evaluation_node(llm)

    graph.add_node("question", question_node)
    graph.add_node("process_answer", answer_processing_node)
    graph.add_node("evaluate", evaluation_node)
    graph.add_node("advance", advance_node)

    # start interview
    graph.set_entry_point("question")

    graph.add_edge("question", "process_answer")
    graph.add_edge("process_answer", "evaluate")
    graph.add_edge("evaluate", "advance")

    return graph.compile()
