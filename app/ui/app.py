# app/ui/app.py

import gradio as gr

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController
from app.ui.views.setup_view import SetupView
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

            # ---------------- WRITTEN ----------------

            with gr.Column(visible=False) as written_container:
                written_question_text = gr.Markdown("")
                written_answer_box = gr.Textbox(label="Your Answer", lines=5)
                written_submit_button = gr.Button("Submit Answer")

            # ---------------- CODING ----------------

            with gr.Column(visible=False) as coding_container:
                coding_question_text = gr.Markdown("")
                coding_answer_box = gr.Textbox(
                    label="Your Code",
                    lines=20,
                    elem_id="code-editor",
                )
                coding_submit_button = gr.Button("Submit Code")

            # ---------------- DATABASE ----------------

            with gr.Column(visible=False) as database_container:
                database_question_text = gr.Markdown("")
                database_answer_box = gr.Textbox(
                    label="Your SQL",
                    lines=10,
                    elem_id="code-editor",
                )
                database_submit_button = gr.Button("Submit SQL")

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
                written_question_text,
                coding_question_text,
                database_question_text,
                written_container,
                coding_container,
                database_container,
                setup_section,
                interview_section,
                completion_section,
                report_section,
            ],
        )

        # =========================================================
        # SUBMIT HANDLERS
        # =========================================================

        written_submit_button.click(
            lambda s, a: submit_answer(controller, s, a),
            inputs=[state, written_answer_box],
            outputs=[
                state,
                question_counter,
                feedback_output,
                written_question_text,
                coding_question_text,
                database_question_text,
                written_container,
                coding_container,
                database_container,
                interview_section,
                completion_section,
            ],
        )

        coding_submit_button.click(
            lambda s, a: submit_answer(controller, s, a),
            inputs=[state, coding_answer_box],
            outputs=[
                state,
                question_counter,
                feedback_output,
                written_question_text,
                coding_question_text,
                database_question_text,
                written_container,
                coding_container,
                database_container,
                interview_section,
                completion_section,
            ],
        )

        database_submit_button.click(
            lambda s, a: submit_answer(controller, s, a),
            inputs=[state, database_answer_box],
            outputs=[
                state,
                question_counter,
                feedback_output,
                written_question_text,
                coding_question_text,
                database_question_text,
                written_container,
                coding_container,
                database_container,
                interview_section,
                completion_section,
            ],
        )

        # =========================================================
        # REPORT
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
