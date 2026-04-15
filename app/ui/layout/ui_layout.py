# app/ui/layout/ui_layout.py

import gradio as gr

from app.ui.views.setup_view import SetupView
from app.ui.views.interview_written_view import InterviewWrittenView
from app.ui.views.interview_coding_view import InterviewCodingView
from app.ui.views.interview_database_view import InterviewDatabaseView

from app.ui.layout.interview_layout_builder import build_interview_views
from app.ui.layout.ui_components import UILayoutComponents

from app.core.build_info import BuildInfo


def build_layout():

    gr.Markdown("# AI Interview Simulator")

    gr.Markdown(BuildInfo.get_info())

    # ---------------------------------------------------------
    # GLOBAL CSS (GitHub-like code style)
    # ---------------------------------------------------------

    gr.HTML(
        """
        <style>
        pre code {
            background-color: #0d1117;
            color: #c9d1d9;
            padding: 16px;
            border-radius: 8px;
            display: block;
            overflow-x: auto;
            font-size: 14px;
            line-height: 1.5;
        }
        </style>
        """
    )

    # ---------------------------------------------------------
    # FOCUS EDITOR ON LOAD
    # ---------------------------------------------------------

    gr.HTML(
        """
            <script>
                function focusEditor() {
                    setTimeout(() => {
                        const editor = document.querySelector('#code-editor textarea');
                        if (editor) {
                            editor.focus();
                        }
                    }, 100);
                }
                window.addEventListener('load', focusEditor);
            </script>
        """
    )

    # ---------------------------------------------------------
    # SCROLL TO TOP ON UI CHANGE
    # ---------------------------------------------------------

    gr.HTML(
        """
            <script>
                function scrollToTop() {
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }

                const observerScroll = new MutationObserver(() => {
                    scrollToTop();
                });

                observerScroll.observe(document.body, { childList: true, subtree: true });
            </script>
        """
    )

    state = gr.State()

    # ---------------------------------------------------------
    # SETUP SECTION
    # ---------------------------------------------------------

    with gr.Column(visible=True) as setup_section:

        setup_view = SetupView()

        (
            role_dropdown,
            interview_type_radio,
            company_input,
            language_dropdown,
            start_button,
            start_loading_text,
        ) = setup_view.render()

    # ---------------------------------------------------------
    # INTERVIEW SECTION
    # ---------------------------------------------------------

    with gr.Column(visible=False) as interview_section:

        question_counter = gr.Markdown("", elem_id="question-counter")

        gr.HTML(
            """
                <script>
                    const observer = new MutationObserver(() => {
                        focusEditor();
                    });
                    observer.observe(document.body, {childList: true, subtree: true});
                </script>
            """
        )

        feedback_output = gr.Markdown(elem_id="feedback-box")

        gr.HTML(
            """
                <style>
                    #feedback-box {
                        padding: 16px;
                        border-radius: 10px;
                        background-color: #111;
                        margin-bottom: 16px;
                    }
                    </style>
            """
        )

        # ---------------------------------------------------------
        # INTERVIEW VIEWS
        # ---------------------------------------------------------

        views = build_interview_views()

        written_container, written_display, written_box, written_submit = views["written"]
        coding_container, coding_display, coding_box, coding_submit = views["coding"]
        database_container, database_display, database_box, database_submit = views["database"]

        # ---------------------------------------------------------
        # ACTIONS
        # ---------------------------------------------------------

        gr.Markdown("---")

        with gr.Row():

            retry_button = gr.Button("Retry Answer", visible=False)
            next_button = gr.Button("Next Question", visible=False)

    # ---------------------------------------------------------
    # COMPLETION SECTION
    # ---------------------------------------------------------

    with gr.Column(visible=False) as completion_section:

        gr.Markdown("## Interview Completed")

        final_feedback = gr.Markdown("")
        view_report_button = gr.Button("View Final Report")

    # ---------------------------------------------------------
    # REPORT SECTION
    # ---------------------------------------------------------

    with gr.Column(visible=False) as report_section:

        report_output = gr.HTML("")

        pdf_button = gr.Button("Download PDF")
        json_button = gr.Button("Download JSON")

        pdf_file = gr.File(visible=False, label="Download PDF Report")
        json_file = gr.File(visible=False, label="Download JSON Report")

        new_interview_button = gr.Button("Start New Interview")

    # ---------------------------------------------------------
    # RETURN COMPONENTS
    # ---------------------------------------------------------

    return UILayoutComponents(
        state=state,
        role_dropdown=role_dropdown,
        interview_type_radio=interview_type_radio,
        company_input=company_input,
        language_dropdown=language_dropdown,
        start_button=start_button,
        start_loading_text=start_loading_text,
        question_counter=question_counter,
        feedback_output=feedback_output,
        written_container=written_container,
        written_display=written_display,
        written_box=written_box,
        written_submit=written_submit,
        coding_container=coding_container,
        coding_display=coding_display,
        coding_box=coding_box,
        coding_submit=coding_submit,
        database_container=database_container,
        database_display=database_display,
        database_box=database_box,
        database_submit=database_submit,
        retry_button=retry_button,
        next_button=next_button,
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
