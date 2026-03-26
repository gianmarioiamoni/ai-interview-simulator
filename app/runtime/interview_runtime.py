# app/runtime/interview_runtime.py

from domain.contracts.interview_state import InterviewState

from app.graph.interview_graph import build_interview_graph
from infrastructure.llm.llm_factory import get_llm
from services.ai_hint_engine.ai_hint_service import AIHintService


_graph = None
_llm = None


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


def get_runtime_graph(llm=None, hint_service=None):

    global _graph

    if _graph is None:

        llm = llm or get_runtime_llm()
        hint_service = hint_service or AIHintService()

        compiled = build_interview_graph(
            llm=llm,  
            hint_service=hint_service,  
        )

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
