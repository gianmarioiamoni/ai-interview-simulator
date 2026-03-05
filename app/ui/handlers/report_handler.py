# app/ui/handlers/report_handler.py

from app.ui.views.report_view import build_report_markdown
from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState
from app.core.flow.interview_flow_engine import InterviewFlowEngine


def view_report_handler(flow_engine: InterviewFlowEngine, state_value):
    # Generates the final report and switches the UI to the report section

    yield (
        *route_ui(UIState.REPORT),
        "⏳ Generating final report...",
    )

    report = flow_engine.generate_report(state_value)

    report_text = build_report_markdown(report)

    yield (
        *route_ui(UIState.REPORT),
        report_text,
    )
