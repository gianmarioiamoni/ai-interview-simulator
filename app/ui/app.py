# app/ui/app.py

import gradio as gr

from app.graph.builder import build_graph
from app.ui.mappers.interview_state_mapper import InterviewStateMapper
from app.ui.controllers.interview_controller import InterviewController

from app.ui.views.setup_view import SetupView
from app.ui.views.interview_written_view import InterviewWrittenView
from app.ui.views.interview_coding_view import InterviewCodingView
from app.ui.views.interview_database_view import InterviewDatabaseView

from app.ui.state_handlers import (
    start_interview,
    submit_answer,
    reset_interview,
    export_pdf,
    export_json,
)

from app.ui.views.report_view import build_report_markdown

from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState


def build_app():

    # Build core services

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
        ui_state = gr.State(UIState.SETUP)

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

            (
                written_container,
                written_text,
                written_box,
                written_submit,
            ) = InterviewWrittenView().build()

            (
                coding_container,
                coding_text,
                coding_box,
                coding_submit,
            ) = InterviewCodingView().build()

            (
                database_container,
                database_text,
                database_box,
                database_submit,
            ) = InterviewDatabaseView().build()

        # =========================================================
        # COMPLETION SECTION
        # =========================================================

        with gr.Column(visible=False) as completion_section:

            gr.Markdown("## Interview Completed")

            final_feedback = gr.Markdown("")

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

            valid = (
                role is not None
                and interview_type is not None
                and company is not None
                and company.strip() != ""
                and language is not None
            )

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

        def start_handler(role, interview_type, company, language):

            (
                state_value,
                question_text,
                counter,
                question_type,
            ) = start_interview(
                controller,
                role,
                interview_type,
                company,
                language,
            )

            written_visible = question_type == "written"
            coding_visible = question_type == "coding"
            database_visible = question_type == "database"

            return (
                state_value,
                counter,
                "",
                question_text,
                question_text,
                question_text,
                gr.update(visible=written_visible),
                gr.update(visible=coding_visible),
                gr.update(visible=database_visible),
                *route_ui(UIState.QUESTION),
            )

        start_button.click(
            start_handler,
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
                written_text,
                coding_text,
                database_text,
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
        # SUBMIT ANSWERS
        # =========================================================

        outputs = [
            state,
            question_counter,
            feedback_output,
            written_text,
            coding_text,
            database_text,
            written_container,
            coding_container,
            database_container,
            setup_section,
            interview_section,
            completion_section,
            report_section,
        ]

        written_submit.click(
            lambda s, a: submit_answer(controller, s, a),
            inputs=[state, written_box],
            outputs=outputs,
        )

        coding_submit.click(
            lambda s, a: submit_answer(controller, s, a),
            inputs=[state, coding_box],
            outputs=outputs,
        )

        database_submit.click(
            lambda s, a: submit_answer(controller, s, a),
            inputs=[state, database_box],
            outputs=outputs,
        )

        # =========================================================
        # REPORT
        # =========================================================

        def view_report_handler(state_value):

            yield (
                *route_ui(UIState.REPORT),
                "⏳ Generating final report...",
            )

            report = controller.generate_final_report(state_value)
            report_text = build_report_markdown(report)

            yield (
                *route_ui(UIState.REPORT),
                report_text,
            )

        view_report_button.click(
            view_report_handler,
            inputs=[state],
            outputs=[
                setup_section,
                interview_section,
                completion_section,
                report_section,
                report_output,
            ],
        )

        # =========================================================
        # EXPORTS
        # =========================================================

        pdf_button.click(
            lambda s: (export_pdf(controller, s), gr.update(visible=True)),
            inputs=[state],
            outputs=[pdf_file, pdf_file],
        )

        json_button.click(
            lambda s: (export_json(controller, s), gr.update(visible=True)),
            inputs=[state],
            outputs=[json_file, json_file],
        )

        # =========================================================
        # RESET
        # =========================================================

        def reset_handler():

            return (
                None,
                *route_ui(UIState.SETUP),
            )

        new_interview_button.click(
            reset_handler,
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
