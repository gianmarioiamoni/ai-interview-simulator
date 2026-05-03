# app/ui/views/interview_coding_view.py

import gradio as gr


class InterviewCodingView:

    def build(self):

        with gr.Group(visible=False) as container:  # ✅ FIX

            code_display = gr.Code(
                label="",
                language="python",
                interactive=False,
                visible=True,
            )

            code_box = gr.Code(
                label="Your Code",
                language="python",
                elem_id="code-editor",
                lines=20,
                interactive=True,
                visible=True,
            )

            submit_button = gr.Button("Submit Code", interactive=False)

        return container, code_display, code_box, submit_button
