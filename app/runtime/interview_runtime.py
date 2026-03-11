# app/runtime/interview_runtime.py

from infrastructure.llm.llm_factory import get_llm
from services.interview_evaluation_service import InterviewEvaluationService
from domain.contracts.interview_state import InterviewState

from app.graph.interview_graph import build_interview_graph

_graph = None
_llm = None
_evaluation_service = None


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

def get_runtime_llm():

    global _llm

    if _llm is None:
        _llm = get_llm()

    return _llm


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------


def get_runtime_graph():

    global _graph

    if _graph is None:

        llm = get_runtime_llm()

        compiled = build_interview_graph(llm)

        original_invoke = compiled.invoke

        def invoke_with_model(state):

            if isinstance(state, dict):
                state = InterviewState.model_validate(state)

            result = original_invoke(state)

            if isinstance(result, dict):
                return InterviewState.model_validate(result)

            return result

        compiled.invoke = invoke_with_model

        _graph = compiled

    return _graph


# ---------------------------------------------------------
# Evaluation Service
# ---------------------------------------------------------

def get_runtime_evaluation_service():

    global _evaluation_service

    if _evaluation_service is None:

        llm = get_runtime_llm()

        _evaluation_service = InterviewEvaluationService(llm)

    return _evaluation_service
