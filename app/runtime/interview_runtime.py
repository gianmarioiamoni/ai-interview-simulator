# app/runtime/interview_runtime.py

from app.graph.interview_graph import build_interview_graph
from infrastructure.llm.llm_factory import get_llm
from services.interview_evaluation_service import InterviewEvaluationService


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

        _graph = build_interview_graph(llm)

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
