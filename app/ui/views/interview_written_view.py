# app/ui/views/interview_written_view.py

import gradio as gr


class InterviewWrittenView:

    # Responsible only for building written question UI

    def build(self):

        with gr.Column(visible=False) as container:

            question_text = gr.Markdown("")

            answer_box = gr.Textbox(
                label="Your Answer",
                lines=5,
            )

            submit_button = gr.Button("Submit Answer")

        return container, question_text, answer_box, submit_button
