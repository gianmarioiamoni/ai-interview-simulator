# app/ui/views/interview_database_view.py

from typing import Callable
from domain.contracts.question import Question
import gradio as gr


class InterviewDatabaseView:

    def __init__(
        self,
        question: Question,
        on_submit: Callable[[str], None],
    ) -> None:
        self._question = question
        self._on_submit = on_submit

    def render(self) -> None:
        gr.Markdown("Database question not implemented yet.")
