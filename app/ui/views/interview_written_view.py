# app/ui/views/interview_written_view.py

from typing import Callable
import gradio as gr
from domain.contracts.question import Question


class InterviewWrittenView:
    # View responsible for rendering written questions

    def __init__(
        self,
        question: Question,
        on_submit: Callable[[str], None],
    ) -> None:

        self._question = question
        self._on_submit = on_submit

    def render(self) -> None:

        gr.Markdown("### Written Question")

        gr.Markdown(self._question.prompt)

        answer_box = gr.Textbox(
            label="Your Answer",
            lines=5,
        )

        submit_button = gr.Button("Submit Answer")

        submit_button.click(
            fn=self._handle_submit,
            inputs=[answer_box],
            outputs=[],
        )

    def _handle_submit(self, answer: str) -> None:

        # Forward answer to controller
        self._on_submit(answer)
