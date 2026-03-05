# app/ui/handlers/report_handler.py

from app.ui.views.report_view import build_report_markdown
from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState


def view_report_handler(controller, state_value):
    # Generates the final report and switches the UI to the report section

    yield (
        *route_ui(UIState.REPORT),
        "⏳ Generating final report...",
    )

    report = controller.generate_final_report(state_value)

    report_text = build_report_markdown(report)

    yield (
        *route_ui(UIState.REPORT),
        report_text,
    )
