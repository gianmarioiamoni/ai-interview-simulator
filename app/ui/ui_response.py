# app/ui/ui_response.py

import gradio as gr
from typing import List, Any
from dataclasses import dataclass


@dataclass
class UIResponse:

    state: object

    role_visible: bool = True
    interview_type_visible: bool = True
    company_visible: bool = True
    language_visible: bool = True
    start_button_visible: bool = True

    page_title: str = "## Configure Your Interview"

    question_counter: str = ""
    feedback_markdown: str = ""

    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

    final_feedback: str = ""
    report_output: str = ""

    show_submit: bool = False
    submit_interactive: bool = False

    show_retry: bool = False
    retry_interactive: bool = True

    show_next: bool = False

    next_label: str = ""
    submit_label: str = "Submit"

    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    written_editor_visible: bool = False
    coding_editor_visible: bool = False
    database_editor_visible: bool = False

    start_button_interactive: bool = False

    loader_visible: bool = False
    loader_value: str = ""

    def to_gradio_outputs(self) -> List[Any]:

        return [
            self.state,
            gr.update(visible=self.role_visible),
            gr.update(visible=self.interview_type_visible),
            gr.update(visible=self.company_visible),
            gr.update(visible=self.language_visible),
            gr.update(
                visible=self.start_button_visible,
                value="Start Interview",
                interactive=self.start_button_interactive,
            ),
            gr.update(value=self.page_title),
            gr.update(value=self.question_counter),
            gr.update(value=self.feedback_markdown),
            gr.update(value=self.written_display, visible=self.written_visible),
            gr.update(value=self.coding_display, visible=self.coding_visible),
            gr.update(value=self.database_display, visible=self.database_visible),
            gr.update(value=self.final_feedback),
            gr.update(value=self.report_output),
            gr.update(
                visible=self.show_submit,
                interactive=self.submit_interactive,
                value=self.submit_label,
            ),
            gr.update(
                visible=self.show_retry,
                interactive=self.retry_interactive,
            ),
            gr.update(
                visible=self.show_next,
                value=self.next_label,
            ),
            gr.update(
                value=self.written_editor_value,
                visible=self.written_editor_visible,
            ),
            gr.update(
                value=self.coding_editor_value,
                visible=self.coding_editor_visible,
            ),
            gr.update(
                value=self.database_editor_value,
                visible=self.database_editor_visible,
            ),
            # 🔥 LOADER (CORRETTO)
            gr.update(
                value=(
                    f"""
                    <div class="loader-box">
                        <div class="spinner"></div>
                        {self.loader_value}
                    </div>
                    """
                    if self.loader_visible
                    else ""
                ),
                elem_classes=["show"] if self.loader_visible else [],
            ),
        ]
