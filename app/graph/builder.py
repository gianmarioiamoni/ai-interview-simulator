# app/graph/builder.py

from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress


class StubInterviewGraph:
    # Minimal stub graph used to unblock UI development.
    # Simulates interview progression without LLM or execution engines.

    def invoke(self, state: InterviewState) -> InterviewState:

        # Setup -> move to in progress
        if state.progress == InterviewProgress.SETUP:
            state.progress = InterviewProgress.IN_PROGRESS
            return state

        # If already completed, return as-is
        if state.progress == InterviewProgress.COMPLETED:
            return state

        # Advance question pointer
        if state.current_question_index < len(state.questions) - 1:
            state.current_question_index += 1
        else:
            state.progress = InterviewProgress.COMPLETED

        return state


def build_graph():
    # Factory function returning the stub graph.
    # Later this will return the real compiled LangGraph.
    return StubInterviewGraph()
