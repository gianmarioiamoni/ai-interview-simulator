# app/ui/handlers/report_handler.py

from domain.contracts.question_evaluation import QuestionEvaluation

from app.runtime.interview_runtime import get_runtime_evaluation_service
from app.ui.views.report_view import build_report_markdown
from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState
from app.ui.dto.final_report_dto import FinalReportDTO


def view_report_handler(state_value):
    # Generates the final interview report and switches the UI to report view.
    # Implemented as a generator to allow progressive UI updates.

    # ---------------------------------------------------------
    # Step 1 — Switch UI to report section with loading message
    # ---------------------------------------------------------

    yield (
        *route_ui(UIState.REPORT),
        "⏳ Generating final report...",
    )

    evaluation_service = get_runtime_evaluation_service()

    # ---------------------------------------------------------
    # Step 2 — Build evaluation ordered list from results
    # ---------------------------------------------------------

    per_question_evaluations = [
        state_value.results_by_question[q.id].evaluation
        for q in state_value.questions
        if q.id in state_value.results_by_question
        and state_value.results_by_question[q.id].evaluation is not None
    ]

    # ---------------------------------------------------------
    # Step 3 — Generate final evaluation only once
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
    # Step 4 — Build report DTO
    # ---------------------------------------------------------

    report = FinalReportDTO.from_state(state_value)

    # ---------------------------------------------------------
    # Step 5 — Render report markdown
    # ---------------------------------------------------------

    report_markdown = build_report_markdown(report)

    # ---------------------------------------------------------
    # Step 6 — Return final UI state
    # ---------------------------------------------------------

    yield (
        *route_ui(UIState.REPORT),
        report_markdown,
    )
