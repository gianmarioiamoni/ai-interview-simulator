# app/ui/views/interview_written_view.py

import gradio as gr


class InterviewWrittenView:

    def render(self):

        question_counter = gr.Markdown("")
        question_text = gr.Markdown("")
        answer_box = gr.Textbox(label="Your Answer", lines=5)
        submit_button = gr.Button("Submit Answer", visible=False)

        return (
            question_counter,
            question_text,
            answer_box,
            submit_button,
        )
