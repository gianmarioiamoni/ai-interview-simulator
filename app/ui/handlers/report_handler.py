# app/ui/handlers/report_handler.py

import gradio as gr

from app.ui.views.report_view import build_report_markdown
from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState
from app.ui.dto.final_report_dto import FinalReportDTO


def view_report_handler(state_value):

    # ---------------------------------------------------------
    # Step 1 — UI loading
    # ---------------------------------------------------------

    yield (
        *route_ui(UIState.REPORT),
        "⏳ Generating final report...",
    )

    # ---------------------------------------------------------
    # Step 2 — Read evaluation from state (graph output)
    # ---------------------------------------------------------

    final_eval = state_value.interview_evaluation

    if final_eval is None:
        raise RuntimeError("Report requested but interview_evaluation is missing")

    # ---------------------------------------------------------
    # Step 3 — Build DTO
    # ---------------------------------------------------------

    report = FinalReportDTO.from_components(
        state=state_value,
        final_evaluation=final_eval,
    )

    # ---------------------------------------------------------
    # Step 4 — Render
    # ---------------------------------------------------------

    report_markdown = build_report_markdown(report)

    # ---------------------------------------------------------
    # Step 5 — Return UI
    # ---------------------------------------------------------

    yield (
        *route_ui(UIState.REPORT),
        report_markdown,
    )
