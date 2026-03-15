# app/ui/ui_router.py

#
# Manages the visibility of the UI sections based on the current UI state.
# QUESTION and FEEDBACK share the same interview page.
#

import gradio as gr
from app.ui.ui_state import UIState


def route_ui(state: UIState):

    setup_visible = state == UIState.SETUP

    interview_visible = state in (
        UIState.QUESTION,
        UIState.FEEDBACK,
    )

    completion_visible = state == UIState.COMPLETION

    report_visible = state == UIState.REPORT

    return (
        gr.update(visible=setup_visible),
        gr.update(visible=interview_visible),
        gr.update(visible=completion_visible),
        gr.update(visible=report_visible),
    )
