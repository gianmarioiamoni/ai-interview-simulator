# app/ui/layout/sections/interview_section.py

import gradio as gr

from app.ui.layout.interview_layout_builder import build_interview_views
from app.ui.layout.assets.CSS import FEEDBACK_BOX_STYLE
from app.ui.layout.assets.scripts import FOCUS_OBSERVER_SCRIPT


def render_interview_section():

    with gr.Column(visible=False) as interview_section:

        question_counter = gr.Markdown("", elem_id="question-counter")

        # JS (from assets)
        gr.HTML(FOCUS_OBSERVER_SCRIPT)

        feedback_output = gr.Markdown(elem_id="feedback-box")

        # CSS (from assets)
        gr.HTML(FEEDBACK_BOX_STYLE)

        views = build_interview_views()

        written_container, written_display, written_box, written_submit = views[
            "written"
        ]
        coding_container, coding_display, coding_box, coding_submit = views["coding"]
        database_container, database_display, database_box, database_submit = views[
            "database"
        ]

        gr.Markdown("---")

        with gr.Row():
            retry_button = gr.Button("Retry Answer", visible=False)
            next_button = gr.Button("Next Question", visible=False)

    return dict(
        interview_section=interview_section,
        question_counter=question_counter,
        feedback_output=feedback_output,
        written_container=written_container,
        written_display=written_display,
        written_box=written_box,
        written_submit=written_submit,
        coding_container=coding_container,
        coding_display=coding_display,
        coding_box=coding_box,
        coding_submit=coding_submit,
        database_container=database_container,
        database_display=database_display,
        database_box=database_box,
        database_submit=database_submit,
        retry_button=retry_button,
        next_button=next_button,
    )
