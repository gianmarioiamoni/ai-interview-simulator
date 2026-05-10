# app/ui/ui_response.py

import gradio as gr
from typing import List, Any
from dataclasses import dataclass

from app.ui.components.loader.loader_renderer import render_loader
from app.ui.mappers.loader_mapper import map_loader_text, map_loader_progress


@dataclass
class UIResponse:

    # =========================================================
    # STATE
    # =========================================================
    state: object

    # =========================================================
    # SETUP COMPONENTS
    # =========================================================
    role_visible: bool = True
    interview_type_visible: bool = True
    company_visible: bool = True
    language_visible: bool = True
    start_button_visible: bool = True
    start_button_interactive: bool = False

    # =========================================================
    # TITLE
    # =========================================================
    page_title: str = "## Configure Your Interview"

    # =========================================================
    # HEADER
    # =========================================================
    question_counter: str = ""
    feedback_markdown: str = ""

    # =========================================================
    # DISPLAY
    # =========================================================
    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

    # =========================================================
    # REPORT
    # =========================================================
    final_feedback: str = ""
    report_output: str = ""

    # =========================================================
    # BUTTONS
    # =========================================================
    show_submit: bool = False
    submit_interactive: bool = False

    show_retry: bool = False
    retry_interactive: bool = True

    show_next: bool = False

    next_label: str = ""
    submit_label: str = "Submit"

    # =========================================================
    # EDITORS
    # =========================================================
    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    written_editor_visible: bool = False
    coding_editor_visible: bool = False
    database_editor_visible: bool = False

    # =========================================================
    # LOADER
    # =========================================================
    loader_visible: bool = False
    loader_value: str = ""
    current_progress: int = 0

    setup_inputs_interactive: bool = True

    # =========================================================
    # OUTPUT CONTRACT (CRITICO)
    # =========================================================
    def to_gradio_outputs(self) -> List[Any]:
        return [
            # 0 STATE
            self.state,
            # 1-5 SETUP INPUTS
            gr.update(visible=self.role_visible, interactive=self.setup_inputs_interactive),
            gr.update(visible=self.interview_type_visible, interactive=self.setup_inputs_interactive),
            gr.update(visible=self.company_visible, interactive=self.setup_inputs_interactive),
            gr.update(visible=self.language_visible, interactive=self.setup_inputs_interactive),
            gr.update(
                visible=self.start_button_visible,
                value="Start Interview",
                interactive=self.start_button_interactive,
            ),
            # 6 TITLE
            gr.update(value=self.page_title),
            # 7-8 HEADER
            gr.update(value=self.question_counter, visible=bool(self.question_counter)),
            gr.update(value=self.feedback_markdown, visible=bool(self.feedback_markdown)),
            # 9-11 DISPLAY
            gr.update(value=self.written_display, visible=self.written_visible),
            gr.update(value=self.coding_display, visible=self.coding_visible),
            gr.update(value=self.database_display, visible=self.database_visible),
            # 12-13 REPORT
            gr.update(value=self.final_feedback, visible=bool(self.final_feedback)),
            gr.update(value=self.report_output, visible=bool(self.report_output)),
            # 14-16 BUTTONS
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
            # 17-19 EDITORS
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
            # index 22 → global_loader
            gr.update(
                visible=self.loader_visible,
                value=(
                    render_loader(self.loader_value, self.current_progress)
                    if self.loader_visible
                    else ""
                ),
            ),
        ]

    def _build_title_with_loader(self, state: object):

        if not getattr(state, "current_step", None):
            return "## Configure Your Interview"

        message = map_loader_text(state.current_step)
        progress = map_loader_progress(state.current_step)

        loader_html = render_loader(message, progress)

        return "## Configure Your Interview\n" f"{loader_html}"
