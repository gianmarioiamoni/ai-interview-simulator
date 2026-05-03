# app/ui/views/interview_written_view.py

import gradio as gr


class InterviewWrittenView:

    def build(self):

        with gr.Group(visible=False) as container:  # ✅ FIX

            question_display = gr.Markdown("")

            answer_box = gr.Textbox(
                label="Your Answer",
                lines=5,
                visible=True,
            )

            submit_button = gr.Button("Submit Answer", interactive=False)

        return container, question_display, answer_box, submit_button
