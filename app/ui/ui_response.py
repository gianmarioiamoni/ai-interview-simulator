# app/ui/ui_response.py

import gradio as gr
from typing import List, Any, Optional
from dataclasses import dataclass

from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState


@dataclass
class UIResponse:

    state: object

    # HEADER
    question_counter: str = ""
    feedback: str = ""

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


    def to_gradio_outputs(self) -> List[Any]:
        # Build the exact output list expected by bindings

        setup_update, interview_update, completion_update, report_update = route_ui(
            self.ui_state
        )

        return [
            # ---------------- STATE
            self.state,
            # ---------------- HEADER / FEEDBACK
            self.question_counter,
            self.feedback,
            # ---------------- DISPLAY (NEW)
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
            gr.update(visible=self.show_retry),
            gr.update(visible=self.show_next, value=self.next_label),
            # ---------------- RESET INPUT BOXES + VISIBILITY
            gr.update(visible=self.written_editor_visible, value=""),
            gr.update(visible=self.coding_editor_visible, value=""),
            gr.update(visible=self.database_editor_visible, value=""),
        ]
