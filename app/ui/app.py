# app/ui/app.py

import gradio as gr

from domain.contracts.role import RoleType

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController
from app.ui.state_handlers import start_interview, submit_answer


def build_app():

    graph = build_graph()
    mapper = InterviewStateMapper()
    controller = InterviewController(graph, mapper)

    with gr.Blocks() as demo:

        gr.Markdown("# AI Interview Simulator")

        state = gr.State()

        # ---------------------------------------------------------
        # Setup Section
        # ---------------------------------------------------------

        with gr.Column(visible=True) as setup_section:

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

            start_button = gr.Button("Start Interview", interactive=False)

        # ---------------------------------------------------------
        # Interview Section
        # ---------------------------------------------------------

        with gr.Column(visible=False) as interview_section:

            question_counter = gr.Markdown("")
            question_text = gr.Markdown("")
            answer_box = gr.Textbox(label="Your Answer", lines=5)
            submit_button = gr.Button("Submit Answer")

        # ---------------------------------------------------------
        # Report Section
        # ---------------------------------------------------------

        with gr.Column(visible=False) as report_section:

            report_output = gr.Markdown()

        # ---------------------------------------------------------
        # Input Validation
        # ---------------------------------------------------------

        def validate_inputs(role, company, language):
            valid = bool(role and company and language)
            return gr.update(interactive=valid)

        role_dropdown.change(
            validate_inputs,
            inputs=[role_dropdown, company_input, language_dropdown],
            outputs=start_button,
        )

        company_input.change(
            validate_inputs,
            inputs=[role_dropdown, company_input, language_dropdown],
            outputs=start_button,
        )

        language_dropdown.change(
            validate_inputs,
            inputs=[role_dropdown, company_input, language_dropdown],
            outputs=start_button,
        )

        # ---------------------------------------------------------
        # Start Interview
        # ---------------------------------------------------------

        start_button.click(
            lambda role, company, language: start_interview(
                controller,
                role,
                company,
                language,
            ),
            inputs=[role_dropdown, company_input, language_dropdown],
            outputs=[
                state,
                question_text,
                question_counter,
                setup_section,
                interview_section,
            ],
        )

        # ---------------------------------------------------------
        # Submit Answer
        # ---------------------------------------------------------

        submit_button.click(
            lambda s, a: submit_answer(controller, s, a),
            inputs=[state, answer_box],
            outputs=[
                state,
                question_text,
                question_counter,
                answer_box,
                interview_section,
                report_section,
                report_output,
            ],
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch()
