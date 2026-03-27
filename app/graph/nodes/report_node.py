# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState
from services.interview_evaluation_service import InterviewEvaluationService
from services.report_builder import ReportBuilder


def report_node(state: InterviewState, service: InterviewEvaluationService) -> InterviewState:

    interview_eval = service.evaluate(
        per_question_evaluations=state.evaluations_list,
        questions=state.questions,
        interview_type=state.interview_type,
        role=state.role.type,
    )

    return ReportBuilder.build(state, interview_eval)
