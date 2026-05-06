# app/ui/handlers/report_handler.py

from app.ui.views.report_view import build_report_markdown
from app.ui.dto.final_report_dto import FinalReportDTO
from app.ui.state_handlers.ui_builder import build_ui_response_from_state


def view_report_handler(state):

    if state.interview_evaluation is None:
        raise RuntimeError("Report requested but interview_evaluation is missing")

    # ---------------------------------------------------------
    # BUILD REPORT (APPLICATION LOGIC, OK HERE)
    # ---------------------------------------------------------

    report = FinalReportDTO.from_components(
        state=state,
        final_evaluation=state.interview_evaluation,
    )

    report_markdown = build_report_markdown(report)

    # ---------------------------------------------------------
    # INJECT INTO STATE (important)
    # ---------------------------------------------------------

    state.report_output = report_markdown

    # ---------------------------------------------------------
    # DELEGATE TO BUILDER
    # ---------------------------------------------------------

    return build_ui_response_from_state(state).to_gradio_outputs()
