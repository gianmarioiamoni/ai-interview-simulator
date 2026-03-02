# app/ui/views/setup_view.py

import gradio as gr

from domain.contracts.role import RoleType
from app.ui.sample_data_loader import load_sample_questions
from domain.contracts.interview_state import InterviewState


class SetupView:
    # Responsible ONLY for collecting user input
    # and producing an InterviewState.

    def __init__(self, controller):
        self._controller = controller

    def render(self, state_component):

        gr.Markdown("## Configure Your Interview")

        role_dropdown = gr.Dropdown(
            choices=[r.name for r in RoleType],
            label="Role",
        )

        company_input = gr.Textbox(
            label="Company", placeholder="e.g. Google, Startup, FinTech..."
        )

        language_dropdown = gr.Dropdown(
            choices=["en", "it"], value="en", label="Language"
        )

        start_button = gr.Button("Start Interview")

        start_button.click(
            self._handle_start,
            inputs=[role_dropdown, company_input, language_dropdown],
            outputs=state_component,
        )

    # ---------------------------------------------------------
    # Internal handler
    # ---------------------------------------------------------

    def _handle_start(
        self,
        role_name: str,
        company: str,
        language: str,
    ):

        role_type = RoleType[role_name]

        questions = load_sample_questions()

        state = InterviewState.create_initial(
            role_type=role_type,
            company=company,
            language=language,
            questions=questions,
            interview_id="session-1",
        )

        return self._controller.start_interview(state)
