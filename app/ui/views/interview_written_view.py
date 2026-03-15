# app/ui/views/interview_written_view.py

import gradio as gr


class InterviewWrittenView:

    # Build UI components for written questions

    def build(self):

        with gr.Column(visible=False) as container:

            question_text = gr.Markdown("")

            answer_box = gr.Textbox(
                label="Your Answer",
                lines=5,
            )

            submit_button = gr.Button("Submit Answer", interactive=False)

        return container, question_text, answer_box, submit_button
