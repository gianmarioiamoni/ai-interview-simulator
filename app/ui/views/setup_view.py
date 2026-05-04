# app/ui/views/setup_view.py

import gradio as gr

from domain.contracts.user.role import RoleType
from domain.contracts.interview.interview_type import InterviewType

from app.ui.layout.assets.styles import LOADER_STYLE


class SetupView:

    def render(self):

        gr.Markdown("## Configure Your Interview")

        gr.HTML(LOADER_STYLE)

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

        # now HTML instead of Markdown
        start_loading_text = gr.HTML("", visible=False)

        return (
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
            start_button,
            start_loading_text,
        )
