# interface/cli/interview_cli_runner.py

from app.graph.interview_graph import build_interview_graph
from domain.contracts.interview_state import InterviewState
from domain.contracts.interview_progress import InterviewProgress


class CLIRunner:

    def __init__(self) -> None:
        self.graph = build_interview_graph()

    def run(self, initial_state: InterviewState) -> InterviewState:
        state = initial_state

        while state.progress != InterviewProgress.COMPLETED:
            state = self.graph.invoke(state)

        return state
