# app/ui/views/interview_written_view.py

import gradio as gr


class InterviewWrittenView:

    # Build UI components for written questions

    def build(self):

        with gr.Column(visible=False) as container:

            # ---------------------------------------------------------
            # Display (question OR user answer)
            # ---------------------------------------------------------

            question_display = gr.Markdown("")

            # ---------------------------------------------------------
            # Input editor (only in QUESTION state)
            # ---------------------------------------------------------

            answer_box = gr.Textbox(
                label="Your Answer",
                lines=5,
                visible=True,
            )

            submit_button = gr.Button("Submit Answer", interactive=False)

        return container, question_display, answer_box, submit_button
