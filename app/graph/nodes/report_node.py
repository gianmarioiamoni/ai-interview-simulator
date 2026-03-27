# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState
from services.interview_evaluation_service import InterviewEvaluationService
from services.report_builder import ReportBuilder

from infrastructure.llm.llm_adapter import DefaultLLMAdapter


def report_node(state: InterviewState) -> InterviewState:

    llm = DefaultLLMAdapter()
    service = InterviewEvaluationService(llm)

    interview_eval = service.evaluate(
        per_question_evaluations=state.evaluations_list,
        questions=state.questions,
        interview_type=state.interview_type,
        role=state.role_type,
    )

    new_state = ReportBuilder.build(state, interview_eval)

    return new_state
