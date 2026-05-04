# app/ui/layout/layout_builder.py

import gradio as gr

from app.ui.layout.ui_components import UILayoutComponents
from app.ui.layout.assets.styles import LOADER_STYLE

from domain.contracts.user.role import RoleType
from domain.contracts.interview.interview_type import InterviewType


class UILayoutBuilder:

    def build(self):

        # ---------------------------------------------------------
        # GLOBAL LOADER
        # ---------------------------------------------------------
        gr.HTML(LOADER_STYLE)

        global_loader = gr.Markdown(
            "",
            visible=False,
            elem_id="global-loader",
        )

        # ---------------------------------------------------------
        # STATE
        # ---------------------------------------------------------
        state = gr.State()

        # ---------------------------------------------------------
        # HEADER
        # ---------------------------------------------------------
        gr.Markdown("# AI Interview Simulator")
        gr.Markdown("Build: 2026-03-16-A | Runtime: HuggingFace Spaces")
        gr.Markdown("---")

        # =========================================================
        # ✅ SETUP CONTAINER (FINAL FIX)
        # =========================================================

        with gr.Column(visible=True) as setup_container:

            gr.Markdown("## Configure Your Interview")

            role_input = gr.Dropdown(
                choices=[(r.name.replace("_", " ").title(), r.value) for r in RoleType],
                label="Role",
            )

            interview_type_input = gr.Radio(
                choices=[t.name for t in InterviewType],
                label="Interview Type",
            )

            company_input = gr.Textbox(label="Company")

            language_input = gr.Dropdown(
                choices=["en", "it"],
                value="en",
                label="Language",
            )

            start_button = gr.Button(
                "Start Interview",
                interactive=False,
            )

        gr.Markdown("---")

        # =========================================================
        # MAIN UI (INTERVIEW)
        # =========================================================

        question_counter = gr.Markdown("")
        feedback_output = gr.Markdown("")

        written_display = gr.Markdown(visible=False)

        coding_display = gr.Code(
            language="python",
            interactive=False,
            visible=False,
        )

        database_display = gr.Code(
            language="sql",
            interactive=False,
            visible=False,
        )

        written_box = gr.Textbox(
            label="Your Answer",
            lines=5,
            visible=False,
        )

        coding_box = gr.Code(
            language="python",
            lines=20,
            visible=False,
        )

        database_box = gr.Code(
            language="sql",
            lines=10,
            visible=False,
        )

        submit_button = gr.Button("Submit", visible=False)
        retry_button = gr.Button("Retry", visible=False)
        next_button = gr.Button("Next", visible=False)

        final_feedback = gr.Markdown("")
        report_output = gr.Markdown("")

        return UILayoutComponents(
            state=state,
            # setup container
            setup_container=setup_container,
            # inputs
            role_input=role_input,
            interview_type_input=interview_type_input,
            company_input=company_input,
            language_input=language_input,
            start_button=start_button,
            # main UI
            question_counter=question_counter,
            feedback_output=feedback_output,
            written_display=written_display,
            coding_display=coding_display,
            database_display=database_display,
            written_box=written_box,
            coding_box=coding_box,
            database_box=database_box,
            submit_button=submit_button,
            retry_button=retry_button,
            next_button=next_button,
            final_feedback=final_feedback,
            report_output=report_output,
            global_loader=global_loader,
        )
