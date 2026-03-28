# app/graph/nodes/report_node.py

from domain.contracts.interview_state import InterviewState
from services.interview_evaluation_service import InterviewEvaluationService


def report_node(
    state: InterviewState,
    service: InterviewEvaluationService,
) -> InterviewState:

    evaluations = state.evaluations_list

    # ---------------------------------------------------------
    # SAFETY: no evaluations → empty report
    # ---------------------------------------------------------

    if not evaluations:
        return state.model_copy(update={"report_output": None})

    interview_eval = service.evaluate(
        per_question_evaluations=evaluations,
        questions=state.questions,
        interview_type=state.interview_type,
        role=state.role.type,
    )

    # ---------------------------------------------------------
    # Build UI-friendly output
    # ---------------------------------------------------------

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
            "interview_evaluation": interview_eval,  # domain
            "report_output": report_output,  # UI
        }
    )
