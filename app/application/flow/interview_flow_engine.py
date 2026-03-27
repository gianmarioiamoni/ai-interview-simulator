# app/application/flow/interview_flow_engine.py

from app.graph.interview_graph import graph
from domain.contracts.interview_state import InterviewState


class InterviewFlowEngine:

    def start(self, state: InterviewState) -> InterviewState:
        # Initial pass through graph
        return graph.invoke(state)

    def next(self, state: InterviewState) -> InterviewState:
        # Set action → let graph handle everything
        state.last_action = "next"
        return graph.invoke(state)

    def retry(self, state: InterviewState) -> InterviewState:
        state.last_action = "retry"
        return graph.invoke(state)
