# app/ui/handlers/report_handler.py

from services.interview_evaluation_service import InterviewEvaluationService

from infrastructure.llm.llm_factory import get_llm

from app.ui.views.report_view import build_report_markdown
from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState
from app.graph.interview_graph import InterviewGraph


def view_report_handler(graph: InterviewGraph, state_value):
    # Generates the final report and switches the UI to the report section

    yield (
        *route_ui(UIState.REPORT),
        "⏳ Generating final report...",
    )

    evaluation_service = InterviewEvaluationService(get_llm())

    report = evaluation_service.evaluate(
        per_question_evaluations=state_value.evaluations,
        questions=state_value.questions,
        interview_type=state_value.interview_type,
        role=state_value.role.type,
    )

    report_text = build_report_markdown(report)

    yield (
        *route_ui(UIState.REPORT),
        report_text,
    )
