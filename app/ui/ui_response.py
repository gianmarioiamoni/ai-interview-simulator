# app/ui/ui_response.py

from __future__ import annotations

import gradio as gr
from typing import TYPE_CHECKING, List, Any, Optional
from dataclasses import dataclass

from app.ui.components.loader.loader_renderer import render_loader
from app.ui.mappers.output_mapper import OutputMapper

if TYPE_CHECKING:
    from app.ui.presentation.candidate_facing_error import CandidateFacingError
    from app.ui.presentation.surface_state import SurfaceState


@dataclass
class UIResponse:

    # STATE
    state: object

    # SETUP
    role_visible: bool = True
    role_custom_name_visible: bool = False
    interview_type_visible: bool = True
    seniority_visible: bool = True
    interview_length_visible: bool = True
    company_visible: bool = True
    language_visible: bool = True
    advanced_context_visible: bool = True
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
    pdf_download_btn_visible: bool = False
    json_download_btn_visible: bool = False

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

    # EPIC-07 ephemeral presentation (not Gradio wire fields)
    candidate_facing_error: Optional["CandidateFacingError"] = None
    surface_state: Optional["SurfaceState"] = None


    # =========================================================
    # DICT CONTRACT
    # =========================================================
    def to_dict(self) -> dict:

        return {
            # 0
            "state": self.state,
            # 1-8 SETUP
            "role_dropdown": gr.update(
                visible=self.role_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "role_custom_name_input": gr.update(
                visible=self.role_custom_name_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "interview_type_radio": gr.update(
                visible=self.interview_type_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "seniority_radio": gr.update(
                visible=self.seniority_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "interview_length_radio": gr.update(
                visible=self.interview_length_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "company_input": gr.update(
                visible=self.company_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "language_dropdown": gr.update(
                visible=self.language_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "enabled_languages_input": gr.update(
                visible=self.language_visible,
                interactive=self.setup_inputs_interactive,
            ),
            "advanced_context_accordion": gr.update(
                visible=self.advanced_context_visible,
            ),
            "start_button": gr.update(
                visible=self.start_button_visible,
                value="Start Interview",
                interactive=self.start_button_interactive,
            ),
            # 6 TITLE
            "page_title": gr.update(value=self.page_title),
            # 7-8 HEADER
            "question_counter": gr.update(
                value=self.question_counter,
                visible=bool(self.question_counter),
            ),
            "feedback_markdown": gr.update(
                value=self.feedback_markdown,
                visible=bool(self.feedback_markdown),
            ),
            # 9-11 DISPLAY
            "written_display": gr.update(
                value=self.written_display,
                visible=self.written_visible,
            ),
            "coding_display": gr.update(
                value=self.coding_display,
                visible=self.coding_visible,
            ),
            "database_display": gr.update(
                value=self.database_display,
                visible=self.database_visible,
            ),
            # 12-14 REPORT
            "final_feedback": gr.update(
                value=self.final_feedback,
                visible=bool(self.final_feedback),
            ),
            "report_output": gr.update(
                value=self.report_output,
                visible=bool(self.report_output),
            ),
            "report_group": gr.update(
                visible=self.report_section_visible,
            ),
            # 15-16 EXPORT BUTTONS
            "pdf_download_btn": gr.DownloadButton(visible=self.pdf_download_btn_visible),
            "json_download_btn": gr.DownloadButton(visible=self.json_download_btn_visible),
            # 15-17 BUTTONS
            "submit_button": gr.update(
                visible=self.show_submit,
                interactive=self.submit_interactive,
                value=self.submit_label,
            ),
            "retry_button": gr.update(
                visible=self.show_retry,
                interactive=self.retry_interactive,
                value=self.retry_label,
            ),
            "next_button": gr.update(
                visible=self.show_next,
                value=self.next_label,
            ),
            # 18-20 EDITORS
            "written_editor": gr.update(
                value=self.written_editor_value,
                visible=self.written_editor_visible,
            ),
            "coding_editor": gr.update(
                value=self.coding_editor_value,
                visible=self.coding_editor_visible,
            ),
            "database_editor": gr.update(
                value=self.database_editor_value,
                visible=self.database_editor_visible,
            ),
            # 21 LOADER
            "loader_html": gr.update(
                visible=self.loader_visible,
                value=(
                    render_loader(
                        self.loader_value,
                        self.current_progress,
                    )
                    if self.loader_visible
                    else ""
                ),
            ),
        }



