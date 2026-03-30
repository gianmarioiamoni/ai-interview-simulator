# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState
from services.interview_evaluation_service import InterviewEvaluationService


def report_node(
    state: InterviewState,
    service: InterviewEvaluationService,
) -> InterviewState:

    results = state.results_by_question or {}

    # ---------------------------------------------------------
    # EXTRACT EVALUATIONS FROM RESULTS
    # ---------------------------------------------------------

    evaluations = [
        result.evaluation
        for result in results.values()
        if result.evaluation is not None
    ]

    # ---------------------------------------------------------
    # SAFETY
    # ---------------------------------------------------------

    if not evaluations:

        return state.model_copy(
            update={
                "interview_evaluation": None,
            }
        )

    # ---------------------------------------------------------
    # NORMAL FLOW
    # ---------------------------------------------------------

    interview_eval = service.evaluate(
        per_question_evaluations=evaluations,
        questions=state.questions,
        interview_type=state.interview_type,
        role=state.role.type,
    )

    return state.model_copy(
        update={
            "interview_evaluation": interview_eval,
        }
    )
