# app/ui/views/setup_view.py

import gradio as gr


class SetupView:

    def __init__(self, on_start):
        self._on_start = on_start

    def render(self, state, controller):

        start_button = gr.Button("Start Interview")

        start_button.click(
            lambda: self._on_start(controller),
            outputs=[
                state,
                self.question_text,
                self.question_counter,
                self.answer_box,
                self.submit_button,
                self.report_output,
            ],
        )

        return start_button
