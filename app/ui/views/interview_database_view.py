# app/ui/views/interview_database_view.py

from typing import Callable
import gradio as gr
from domain.contracts.question import Question


class InterviewDatabaseView:
    # View responsible for rendering database questions

    def __init__(
        self,
        question: Question,
        on_submit: Callable[[str], None],
    ) -> None:

        self._question = question
        self._on_submit = on_submit

    def render(self) -> None:

        gr.Markdown("### Database Question")

        gr.Markdown(self._question.prompt)

        sql_box = gr.Textbox(
            elem_id="code-editor",
            label="Your SQL",
            lines=10,
        )

        submit_button = gr.Button("Submit SQL")

        submit_button.click(
            fn=self._handle_submit,
            inputs=[sql_box],
            outputs=[],
        )

    def _handle_submit(self, sql: str) -> None:

        self._on_submit(sql)
