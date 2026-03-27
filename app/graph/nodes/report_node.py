# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState
from services.interview_evaluation_service import InterviewEvaluationService


def report_node(
    state: InterviewState,
    service: InterviewEvaluationService,
) -> InterviewState:

    evaluations = state.evaluations_list

    # ---------------------------------------------------------
    # SAFETY: no evaluations → skip report
    # ---------------------------------------------------------

    if not evaluations:
        return state

    interview_eval = service.evaluate(
        per_question_evaluations=evaluations,
        questions=state.questions,
        interview_type=state.interview_type,
        role=state.role.type, 
    )

    return state.model_copy(update={"final_evaluation": interview_eval})
