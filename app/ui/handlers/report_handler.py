# app/ui/handlers/report_handler.py

from app.runtime.interview_runtime import get_runtime_evaluation_service
from app.ui.views.report_view import build_report_markdown
from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState


def view_report_handler(state_value):
    # Generates the final report and switches the UI to the report section

    yield (
        *route_ui(UIState.REPORT),
        "⏳ Generating final report...",
    )

    evaluation_service = get_runtime_evaluation_service()

    # ---------------------------------------------------------
    # Extract question evaluations from results_by_question
    # ---------------------------------------------------------

    per_question_evaluations = []

    for result in state_value.results_by_question.values():
        if result.evaluation is not None:
            per_question_evaluations.append(result.evaluation)

    # ---------------------------------------------------------
    # Generate final evaluation only once
    # ---------------------------------------------------------

    if state_value.final_evaluation is None:

        final_eval = evaluation_service.evaluate(
            per_question_evaluations=per_question_evaluations,
            questions=state_value.questions,
            interview_type=state_value.interview_type,
            role=state_value.role.type,
        )

        state_value.final_evaluation = final_eval

    # ---------------------------------------------------------
    # Build final report DTO and markdown
    # ---------------------------------------------------------

    from app.ui.state_handlers import mapper

    report = mapper.to_final_report_dto(state_value)

    report_text = build_report_markdown(report)

    yield (
        *route_ui(UIState.REPORT),
        report_text,
    )
