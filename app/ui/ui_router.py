# app/ui/ui_router.py

#
# It manages the visibility of the UI sections based on the current state.
#
import gradio as gr
from app.ui.ui_state import UIState


def route_ui(state: UIState):

    setup_visible = state == UIState.SETUP
    interview_visible = state == UIState.QUESTION
    completion_visible = state == UIState.COMPLETION
    report_visible = state == UIState.REPORT

    return (
        gr.update(visible=setup_visible),
        gr.update(visible=interview_visible),
        gr.update(visible=completion_visible),
        gr.update(visible=report_visible),
    )
