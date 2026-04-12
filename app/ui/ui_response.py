# app/ui/ui_response.py

import gradio as gr
from typing import List, Any, Optional
from dataclasses import dataclass

from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState
from domain.contracts.feedback.quality import Quality


@dataclass
class UIResponse:

    state: object

    # HEADER
    question_counter: str = ""

    # FEEDBACK
    feedback_markdown: str = ""
    feedback_quality: Optional[Quality] = None

    # DISPLAY
    written_display: str = ""
    coding_display: str = ""
    database_display: str = ""

    # CONTAINERS
    written_visible: bool = False
    coding_visible: bool = False
    database_visible: bool = False

    # EDITORS
    written_editor_visible: bool = False
    coding_editor_visible: bool = False
    database_editor_visible: bool = False

    # RETRY
    retry_interactive: bool = True
    retry_label: Optional[str] = None 

    # STATE
    ui_state: Optional[UIState] = None

    # REPORT
    final_feedback: str = ""
    report_output: str = ""

    # BUTTONS
    show_submit: bool = True
    show_retry: bool = False
    show_next: bool = False
    next_label: str = "Next Question"
    show_submit_interactive: bool = False

    # EDITOR VALUES
    written_editor_value: str = ""
    coding_editor_value: str = ""
    database_editor_value: str = ""

    # LOADER
    loader_visible: bool = False
    loader_value: str = ""

    def to_gradio_outputs(self) -> List[Any]:

        setup_update, interview_update, completion_update, report_update = route_ui(
            self.ui_state
        )

        return [
            # ---------------- STATE
            self.state,
            # ---------------- HEADER / FEEDBACK
            self.question_counter,
            self.feedback_markdown,  # ✅ FIX
            # ---------------- DISPLAY
            self.written_display,
            self.coding_display,
            self.database_display,
            # ---------------- CONTAINERS VISIBILITY
            gr.update(visible=self.written_visible),
            gr.update(visible=self.coding_visible),
            gr.update(visible=self.database_visible),
            # ---------------- SECTIONS
            setup_update,
            interview_update,
            completion_update,
            report_update,
            # ---------------- COMPLETION / REPORT
            self.final_feedback,
            self.report_output,
            # ---------------- BUTTONS
            gr.update(
                visible=self.show_submit,
                interactive=self.show_submit_interactive,
            ),
            gr.update(
                visible=self.show_retry,
                interactive=self.retry_interactive,
            ),
            gr.update(
                visible=self.show_next,
                value=self.next_label,
            ),
            # ---------------- EDITORS
            gr.update(
                visible=self.written_editor_visible,
                value=self.written_editor_value if self.written_editor_visible else "",
            ),
            gr.update(
                visible=self.coding_editor_visible,
                value=self.coding_editor_value if self.coding_editor_visible else "",
            ),
            gr.update(
                visible=self.database_editor_visible,
                value=(
                    self.database_editor_value if self.database_editor_visible else ""
                ),
            ),
            # ---------------- LOADER
            gr.update(
                visible=self.loader_visible,
                value=self.loader_value if self.loader_visible else "",
            ) if self.loader_visible else gr.update(visible=False),
        ]
