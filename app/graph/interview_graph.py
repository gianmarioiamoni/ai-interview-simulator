# app/graph/interview_graph.py

from langgraph.graph import StateGraph, END

from domain.contracts.interview_state import InterviewState

from app.graph.nodes.question_node import question_node
from app.graph.nodes.answer_processing_node import answer_processing_node
from app.graph.nodes.evaluation_node import evaluation_node
from app.graph.nodes.flow_node import flow_node


def build_interview_graph():

    graph = StateGraph(InterviewState)

    graph.add_node("question", question_node)
    graph.add_node("process", answer_processing_node)
    graph.add_node("evaluate", evaluation_node)
    graph.add_node("flow", flow_node)

    graph.set_entry_point("question")

    graph.add_edge("process", "evaluate")
    graph.add_edge("evaluate", "flow")
    graph.add_edge("flow", "question")

    graph.add_edge("question", END)

    compiled = graph.compile()

    original_invoke = compiled.invoke

    def invoke_with_model(state):

        if isinstance(state, dict):
            state = InterviewState.model_validate(state)

        result = original_invoke(state)

        if isinstance(result, dict):
            return InterviewState.model_validate(result)

        return result

    compiled.invoke = invoke_with_model

    return compiled
