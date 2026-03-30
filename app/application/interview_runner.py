# app/application/interview_runner.py

from domain.contracts.interview_state import InterviewState

from app.graph.interview_graph import run_graph
from app.runtime.interview_runtime import get_runtime_llm


def create_interview_runner():

    llm = get_runtime_llm()

    def run(state: InterviewState) -> InterviewState:
        return run_graph(
            llm=llm,
            state=state,
        )

    return run
