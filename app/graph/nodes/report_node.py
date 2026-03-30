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
    # SAFETY: no evaluations → empty structured report
    # ---------------------------------------------------------

    if not evaluations:

        empty_report = {
            "overall_score": 0,
            "hiring_probability": 0,
            "percentile_rank": 0,
            "confidence": 0.0,
            "executive_summary": "No evaluation available",
            "improvement_suggestions": [],
        }

        return state.model_copy(
            update={
                "interview_evaluation": None,
                "report_output": empty_report,
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

    report_output = {
        "overall_score": interview_eval.overall_score,
        "hiring_probability": interview_eval.hiring_probability,
        "percentile_rank": interview_eval.percentile_rank,
        "confidence": interview_eval.confidence.final,
        "executive_summary": interview_eval.executive_summary,
        "improvement_suggestions": interview_eval.improvement_suggestions,
    }

    return state.model_copy(
        update={
            "interview_evaluation": interview_eval,
            "report_output": report_output,
        }
    )
