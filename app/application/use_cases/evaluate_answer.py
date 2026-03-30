# app/application/use_cases/evaluate_answer.py

from domain.contracts.interview_state import InterviewState

from app.runtime.interview_runtime import get_runtime_graph
from services.ai_hint_engine.ai_hint_service import AIHintService


class EvaluateAnswerUseCase:

    def __init__(
        self,
        llm,
        interview_graph=None,
        hint_service=None,
    ):
        self.llm = llm
        self.hint_service = hint_service or AIHintService()

        # ---------------------------------------------------------
        # GRAPH INJECTION STRATEGY
        # ---------------------------------------------------------

        if interview_graph is not None:
            self.interview_graph = interview_graph
        else:
            self.interview_graph = get_runtime_graph(llm, self.hint_service)

    # ---------------------------------------------------------

    def execute(self, state: InterviewState) -> InterviewState:

        result = self.interview_graph.invoke(state)

        if isinstance(result, InterviewState):
            return result

        return InterviewState.model_validate(result)
