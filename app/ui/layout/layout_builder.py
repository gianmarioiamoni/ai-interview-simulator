# app/ui/layout/layout_builder.py

import gradio as gr

from app.ui.layout.ui_components import UILayoutComponents

from .sections.header_section import render_header
from .sections.setup_section import render_setup_section
from .sections.interview_section import render_interview_section
from .sections.completion_section import render_completion_section
from .sections.report_section import render_report_section


class UILayoutBuilder:

    def build(self):

        render_header()

        state = gr.State()

        setup = render_setup_section()
        interview = render_interview_section()
        completion = render_completion_section()
        report = render_report_section()

        return UILayoutComponents(
            state=state,
            **setup,
            **interview,
            **completion,
            **report,
        )
