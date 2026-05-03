# app/ui/ui_response.py

import gradio as gr
from typing import List, Any
from dataclasses import dataclass


@dataclass
class UIResponse:

    state: object

    question_counter: str = ""
    feedback_markdown: str = ""

    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    final_feedback: str = ""
    report_output: str = ""

    show_submit: bool = False
    show_submit_interactive: bool = False
    show_retry: bool = False
    show_next: bool = False
    next_label: str = "Next"

    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    loader_visible: bool = False
    loader_value: str = ""

    def to_gradio_outputs(self) -> List[Any]:

        return [
            self.state,
            self.question_counter,
            gr.update(value=self.feedback_markdown),
            self.written_display,
            self.coding_display,
            self.database_display,
            self.final_feedback,
            self.report_output,
            gr.update(
                visible=self.show_submit, interactive=self.show_submit_interactive
            ),
            gr.update(visible=self.show_retry),
            gr.update(visible=self.show_next, value=self.next_label),
            gr.update(value=self.written_editor_value),
            gr.update(value=self.coding_editor_value),
            gr.update(value=self.database_editor_value),
            gr.update(visible=self.loader_visible, value=self.loader_value),
        ]
