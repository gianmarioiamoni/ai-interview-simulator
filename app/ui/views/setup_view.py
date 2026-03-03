# app/ui/views/setup_view.py

import gradio as gr

from domain.contracts.role import RoleType
from domain.contracts.interview_type import InterviewType
from domain.contracts.interview_state import InterviewState

from app.ui.sample_data_loader import load_sample_questions
from app.ui.controllers.interview_controller import InterviewController


class SetupView:
    # 
    # Responsible ONLY for:
    # - Collecting setup input
    # - Creating InterviewState
    # - Calling controller.start_interview

    def __init__(self, controller: InterviewController):
        self._controller = controller

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, state_component):

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

        # ---------------------------
        # Input validation
        # ---------------------------

        def validate(role, interview_type, company, language):
            valid = bool(role and interview_type and company and language)
            return gr.update(interactive=valid)

        for component in [
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
        ]:
            component.change(
                validate,
                inputs=[
                    role_dropdown,
                    interview_type_radio,
                    company_input,
                    language_dropdown,
                ],
                outputs=start_button,
            )

        # ---------------------------
        # Start handler
        # ---------------------------

        start_button.click(
            self._handle_start,
            inputs=[
                role_dropdown,
                interview_type_radio,
                company_input,
                language_dropdown,
            ],
            outputs=[
                state_component,
                # Below outputs will be filled by app.py wiring
            ],
        )

        return (
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
            start_button,
        )

    # =========================================================
    # HANDLE START
    # =========================================================

    def _handle_start(
        self,
        role_name: str,
        interview_type_name: str,
        company: str,
        language: str,
    ):

        role_type = RoleType[role_name]
        interview_type = InterviewType[interview_type_name]

        questions = load_sample_questions(interview_type)

        state = InterviewState.create_initial(
            role_type=role_type,
            interview_type=interview_type,
            company=company,
            language=language,
            questions=questions,
            interview_id="session-1",
        )

        session_dto = self._controller.start_interview(state)

        return (
            state,
            session_dto.current_question.text,
            f"Question {session_dto.current_question.index}/{session_dto.current_question.total}",
            "",
            gr.update(visible=False),
            gr.update(visible=True),
            gr.update(visible=False),
            gr.update(visible=False),
        )
