import gradio as gr


class InterviewCodingView:

    # Build UI components for coding questions

    def build(self):

        with gr.Column(visible=False) as container:

            question_text = gr.Markdown("")

            # ---------------------------------------------------------
            # Code editor
            # ---------------------------------------------------------

            code_box = gr.Code(
                label="Your Code",
                language="python",
                elem_id="code-editor",
                lines=20,
                interactive=True,
            )

            submit_button = gr.Button("Submit Code")

        return container, question_text, code_box, submit_button
