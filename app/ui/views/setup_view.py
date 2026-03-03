# app/ui/views/setup_view.py

import gradio as gr

from domain.contracts.role import RoleType
from domain.contracts.interview_type import InterviewType


class SetupView:
    """
    Responsible ONLY for rendering setup UI.
    No controller logic here.
    """

    def render(self):

        gr.Markdown("## Configure Your Interview")

        role_dropdown = gr.Dropdown(
            choices=[(r.name.replace("_", " "), r.name) for r in RoleType],
            label="Role",
        )

        interview_type_radio = gr.Radio(
            choices=[t.name for t in InterviewType],
            label="Interview Type",
        )

        company_input = gr.Textbox(
            label="Company",
            placeholder="e.g. Google, Startup, FinTech...",
        )

        language_dropdown = gr.Dropdown(
            choices=["en", "it"],
            value="en",
            label="Language",
        )

        start_button = gr.Button("Start Interview", interactive=False)

        return (
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
            start_button,
        )
