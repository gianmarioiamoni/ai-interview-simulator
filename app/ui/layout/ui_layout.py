# app/ui/layout/ui_layout.py

import gradio as gr

from app.ui.views.setup_view import SetupView
from app.ui.views.interview_written_view import InterviewWrittenView
from app.ui.views.interview_coding_view import InterviewCodingView
from app.ui.views.interview_database_view import InterviewDatabaseView

from app.ui.layout.ui_components import UILayoutComponents


def build_layout():

    gr.Markdown("# AI Interview Simulator")

    state = gr.State()

    with gr.Column(visible=True) as setup_section:

        setup_view = SetupView()

        (
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
            start_button,
        ) = setup_view.render()

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

    with gr.Column(visible=False) as completion_section:

        gr.Markdown("## Interview Completed")

        final_feedback = gr.Markdown("")
        view_report_button = gr.Button("View Final Report")

    with gr.Column(visible=False) as report_section:

        report_output = gr.Markdown("")

        pdf_button = gr.Button("Download PDF")
        json_button = gr.Button("Download JSON")

        pdf_file = gr.File(visible=False)
        json_file = gr.File(visible=False)

        new_interview_button = gr.Button("Start New Interview")

    return UILayoutComponents(
        state=state,
        role_dropdown=role_dropdown,
        interview_type_radio=interview_type_radio,
        company_input=company_input,
        language_dropdown=language_dropdown,
        start_button=start_button,
        question_counter=question_counter,
        feedback_output=feedback_output,
        written_container=written_container,
        written_text=written_text,
        written_box=written_box,
        written_submit=written_submit,
        coding_container=coding_container,
        coding_text=coding_text,
        coding_box=coding_box,
        coding_submit=coding_submit,
        database_container=database_container,
        database_text=database_text,
        database_box=database_box,
        database_submit=database_submit,
        setup_section=setup_section,
        interview_section=interview_section,
        completion_section=completion_section,
        report_section=report_section,
        final_feedback=final_feedback,
        view_report_button=view_report_button,
        pdf_button=pdf_button,
        json_button=json_button,
        pdf_file=pdf_file,
        json_file=json_file,
        new_interview_button=new_interview_button,
        report_output=report_output,
    )
