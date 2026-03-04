# app/ui/views/interview_coding_view.py

import gradio as gr


class InterviewCodingView:

    # Build UI components for coding questions

    def build(self):

        with gr.Column(visible=False) as container:

            question_text = gr.Markdown("")

            code_box = gr.Textbox(
                label="Your Code",
                elem_id="code-editor",
                lines=20,
            )

            submit_button = gr.Button("Submit Code")

        return container, question_text, code_box, submit_button
