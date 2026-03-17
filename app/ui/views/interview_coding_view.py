# app/ui/views/interview_coding_view.py

import gradio as gr


class InterviewCodingView:

    # Build UI components for coding questions

    def build(self):

        with gr.Column(visible=False) as container:

            # ---------------------------------------------------------
            # Display (question OR user answer)
            # ---------------------------------------------------------

            question_display = gr.Markdown("")

            # ---------------------------------------------------------
            # Code editor (only in QUESTION state)
            # ---------------------------------------------------------

            code_box = gr.Code(
                label="Your Code",
                language="python",
                elem_id="code-editor",
                lines=20,
                interactive=True,
                visible=True,
            )

            submit_button = gr.Button("Submit Code", interactive=False)

        return container, question_display, code_box, submit_button
