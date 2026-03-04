# app/ui/app.py

import gradio as gr

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController
from app.ui.views.setup_view import SetupView
from app.ui.views.interview_view_factory import InterviewViewFactory
from app.ui.state_handlers import (
    start_interview,
    submit_answer,
    reset_interview,
    export_pdf,
    export_json,
)
from app.ui.views.report_view import build_report_markdown


def build_app():

    graph = build_graph()
    mapper = InterviewStateMapper()
    controller = InterviewController(graph, mapper)

    with gr.Blocks(
        css="""
        #code-editor textarea {
            font-family: monospace;
        }
        """
    ) as demo:

        gr.Markdown("# AI Interview Simulator")

        state = gr.State()

        # =========================================================
        # SETUP SECTION
        # =========================================================

        with gr.Column(visible=True) as setup_section:

            setup_view = SetupView()

            (
                role_dropdown,
                interview_type_radio,
                company_input,
                language_dropdown,
                start_button,
            ) = setup_view.render()

        # =========================================================
        # INTERVIEW SECTION
        # =========================================================

        with gr.Column(visible=False) as interview_section:

            question_counter = gr.Markdown("")
            feedback_output = gr.Markdown("")

            # Dynamic container where the specific view will render
            with gr.Column() as dynamic_question_container:
                pass

        # =========================================================
        # COMPLETION SECTION
        # =========================================================

        with gr.Column(visible=False) as completion_section:

            gr.Markdown("## Interview Completed")
            view_report_button = gr.Button("View Final Report")

        # =========================================================
        # REPORT SECTION
        # =========================================================

        with gr.Column(visible=False) as report_section:

            report_output = gr.Markdown("")

            pdf_button = gr.Button("Download PDF")
            json_button = gr.Button("Download JSON")

            pdf_file = gr.File(visible=False)
            json_file = gr.File(visible=False)

            new_interview_button = gr.Button("Start New Interview")

        # =========================================================
        # INPUT VALIDATION
        # =========================================================

        def validate_inputs(role, interview_type, company, language):
            valid = bool(role and interview_type and company and language)
            return gr.update(interactive=valid)

        for component in [
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
        ]:
            component.change(
                validate_inputs,
                inputs=[
                    role_dropdown,
                    interview_type_radio,
                    company_input,
                    language_dropdown,
                ],
                outputs=start_button,
            )

        # =========================================================
        # RENDER QUESTION (FACTORY DRIVEN)
        # =========================================================

        def render_question(session_dto):

            question = session_dto.current_question

            with dynamic_question_container:
                gr.Markdown(f"### Question {session_dto.current_index + 1}")
                gr.Markdown(question.prompt)

                view = InterviewViewFactory.create(
                    question=question,
                    on_submit=lambda answer: submit_answer(
                        controller,
                        session_dto.state,
                        answer,
                    ),
                )

                view.render()

        # =========================================================
        # START INTERVIEW
        # =========================================================

        start_button.click(
            lambda role, interview_type, company, language: start_interview(
                controller,
                role,
                interview_type,
                company,
                language,
            ),
            inputs=[
                role_dropdown,
                interview_type_radio,
                company_input,
                language_dropdown,
            ],
            outputs=[
                state,
                question_counter,
                feedback_output,
                setup_section,
                interview_section,
                completion_section,
                report_section,
            ],
        )

        # =========================================================
        # VIEW REPORT
        # =========================================================

        def view_report_handler(state_value):

            yield (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                "⏳ Generating final report...",
            )

            report = controller.generate_final_report(state_value)
            report_text = build_report_markdown(report)

            yield (
                gr.update(visible=False),
                gr.update(visible=False),
                gr.update(visible=True),
                report_text,
            )

        view_report_button.click(
            view_report_handler,
            inputs=[state],
            outputs=[
                interview_section,
                completion_section,
                report_section,
                report_output,
            ],
            show_progress=True,
        )

        # =========================================================
        # EXPORTS
        # =========================================================

        pdf_button.click(
            lambda s: (export_pdf(controller, s), gr.update(visible=True)),
            inputs=[state],
            outputs=[pdf_file, pdf_file],
            show_progress=True,
        )

        json_button.click(
            lambda s: (export_json(controller, s), gr.update(visible=True)),
            inputs=[state],
            outputs=[json_file, json_file],
            show_progress=True,
        )

        # =========================================================
        # RESET
        # =========================================================

        new_interview_button.click(
            reset_interview,
            outputs=[
                state,
                setup_section,
                interview_section,
                completion_section,
                report_section,
            ],
        )

    return demo


if __name__ == "__main__":
    app = build_app()
    app.launch()
