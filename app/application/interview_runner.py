# app/application/interview_runner.py

from domain.contracts.interview_state import InterviewState

from app.graph.interview_graph import build_interview_graph
from app.runtime.interview_runtime import get_runtime_llm
from services.ai_hint_engine.ai_hint_service import AIHintService


def create_interview_runner():

    llm = get_runtime_llm()
    hint_service = AIHintService()

    def run(state: InterviewState) -> InterviewState:
        return build_interview_graph(
            llm=llm,
            hint_service=hint_service,
        ).invoke(state)

    return run
