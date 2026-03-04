# app/ui/views/interview_coding_view.py

from typing import Callable
import gradio as gr
from domain.contracts import Question


class InterviewCodingView:
    # View responsible only for rendering coding questions

    def __init__(
        self,
        question: Question,
        on_submit: Callable[[str], None],
    ) -> None:
        self._question = question
        self._on_submit = on_submit

    def render(self) -> None:
        # Render coding question UI

        gr.Markdown(f"### Coding Question")
        gr.Markdown(self._question.prompt)

        code_input = gr.Textbox(
            elem_id="code-editor",
            label="Your Code",
            lines=20,
            max_lines=30,
            show_label=True,
            interactive=True,
            elem_classes=["monospace"],
        )

        submit_button = gr.Button("Submit")

        submit_button.click(
            fn=self._handle_submit,
            inputs=[code_input],
            outputs=[],
        )

    def _handle_submit(self, code: str) -> None:
        # Forward answer to controller
        self._on_submit(code)
