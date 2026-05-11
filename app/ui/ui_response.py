# app/ui/ui_response.py

import gradio as gr
from typing import List, Any
from dataclasses import dataclass

from app.ui.components.loader.loader_renderer import render_loader


@dataclass
class UIResponse:

    # STATE
    state: object

    # SETUP
    role_visible: bool = True
    interview_type_visible: bool = True
    company_visible: bool = True
    language_visible: bool = True
    start_button_visible: bool = True
    start_button_interactive: bool = False

    # TITLE
    page_title: str = "## Configure Your Interview"

    # HEADER
    question_counter: str = ""
    feedback_markdown: str = ""

    # DISPLAY
    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

    # REPORT
    final_feedback: str = ""
    report_output: str = ""
    report_section_visible: bool = False

    # BUTTONS
    show_submit: bool = False
    submit_interactive: bool = False

    show_retry: bool = False
    retry_interactive: bool = True
    retry_label: str = "Retry"

    show_next: bool = False
    next_label: str = ""
    submit_label: str = "Submit"

    # EDITORS
    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    written_editor_visible: bool = False
    coding_editor_visible: bool = False
    database_editor_visible: bool = False

    # LOADER
    loader_visible: bool = False
    loader_value: str = ""
    current_progress: int = 0

    setup_inputs_interactive: bool = True

    # =========================================================
    # OUTPUT CONTRACT (ALLINEATO)
    # =========================================================
    def to_gradio_outputs(self) -> List[Any]:
        return [
            # 0 STATE
            self.state,
            # 1-5 SETUP INPUTS
            gr.update(
                visible=self.role_visible, interactive=self.setup_inputs_interactive
            ),
            gr.update(
                visible=self.interview_type_visible,
                interactive=self.setup_inputs_interactive,
            ),
            gr.update(
                visible=self.company_visible, interactive=self.setup_inputs_interactive
            ),
            gr.update(
                visible=self.language_visible, interactive=self.setup_inputs_interactive
            ),
            gr.update(
                visible=self.start_button_visible,
                value="Start Interview",
                interactive=self.start_button_interactive,
            ),
            # 6 TITLE
            gr.update(value=self.page_title),
            # 7-8 HEADER
            gr.update(value=self.question_counter, visible=bool(self.question_counter)),
            gr.update(
                value=self.feedback_markdown, visible=bool(self.feedback_markdown)
            ),
            # 9-11 DISPLAY
            gr.update(value=self.written_display, visible=self.written_visible),
            gr.update(value=self.coding_display, visible=self.coding_visible),
            gr.update(value=self.database_display, visible=self.database_visible),
            # 12-14 REPORT
            gr.update(value=self.final_feedback, visible=bool(self.final_feedback)),
            gr.update(value=self.report_output, visible=bool(self.report_output)),
            gr.update(visible=self.report_section_visible),
            # 15-17 BUTTONS
            gr.update(
                visible=self.show_submit,
                interactive=self.submit_interactive,
                value=self.submit_label,
            ),
            gr.update(
                visible=self.show_retry,
                interactive=self.retry_interactive,
                value=self.retry_label,
            ),
            gr.update(
                visible=self.show_next,
                value=self.next_label,
            ),
            # 18-20 EDITORS
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
            # 21 LOADER
            gr.update(
                visible=self.loader_visible,
                value=(
                    render_loader(self.loader_value, self.current_progress)
                    if self.loader_visible
                    else ""
                ),
            ),
        ]
