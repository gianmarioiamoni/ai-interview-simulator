# app/ui/views/interview_coding_view.py

from typing import Callable
import gradio as gr

from app.ui.dto.question_dto import QuestionDTO


class InterviewCodingView:
    # View responsible only for rendering coding questions

    def __init__(
        self,
        question: QuestionDTO,
        on_submit: Callable[[str], None],
    ) -> None:

        self._question = question
        self._on_submit = on_submit

    def render(self) -> None:

        gr.Markdown("### Coding Question")

        gr.Markdown(self._question.text)

        code_input = gr.Textbox(
            elem_id="code-editor",
            label="Your Code",
            lines=20,
            max_lines=30,
            interactive=True,
        )

        submit_button = gr.Button("Submit Code")

        submit_button.click(
            fn=self._handle_submit,
            inputs=[code_input],
            outputs=[],
        )

    def _handle_submit(self, code: str) -> None:

        self._on_submit(code)
