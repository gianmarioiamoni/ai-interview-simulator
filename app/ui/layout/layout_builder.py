# app/ui/layout/layout_builder.py

import gradio as gr

from app.ui.layout.ui_components import UILayoutComponents


class UILayoutBuilder:

    def build(self):

        # ---------------------------------------------------------
        # STATE
        # ---------------------------------------------------------
        state = gr.State()

        # ---------------------------------------------------------
        # HEADER
        # ---------------------------------------------------------
        question_counter = gr.Markdown("")
        feedback_output = gr.Markdown("")

        # ---------------------------------------------------------
        # DISPLAY (UNIFIED)
        # ---------------------------------------------------------
        written_display = gr.Markdown("")
        coding_display = gr.Code(language="python", interactive=False)
        database_display = gr.Code(language="sql", interactive=False)

        # ---------------------------------------------------------
        # EDITORS
        # ---------------------------------------------------------
        written_box = gr.Textbox(label="Your Answer", lines=5)
        coding_box = gr.Code(language="python", lines=20)
        database_box = gr.Code(language="sql", lines=10)

        # ---------------------------------------------------------
        # BUTTONS
        # ---------------------------------------------------------
        submit_button = gr.Button("Submit", visible=False)
        retry_button = gr.Button("Retry", visible=False)
        next_button = gr.Button("Next", visible=False)

        # ---------------------------------------------------------
        # REPORT
        # ---------------------------------------------------------
        final_feedback = gr.Markdown("")
        report_output = gr.Markdown("")

        # ---------------------------------------------------------
        # LOADER
        # ---------------------------------------------------------
        global_loader = gr.Markdown("", visible=False)

        return UILayoutComponents(
            state=state,
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
