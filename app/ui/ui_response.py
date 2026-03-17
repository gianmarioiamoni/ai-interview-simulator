# app/ui/ui_response.py

import gradio as gr
from typing import List, Any

from app.ui.ui_router import route_ui
from app.ui.ui_state import UIState


class UIResponse:
    # Encapsulates UI updates to avoid fragile long tuples

    def __init__(
        self,
        state,
        question_counter: str = "",
        feedback: str = "",
        # ---------------- DISPLAY (NEW)
        written_display: str = "",
        coding_display: str = "",
        database_display: str = "",
        # ---------------- LEGACY TEXT (can be deprecated later)
        written_text: str = "",
        coding_text: str = "",
        database_text: str = "",
        # ---------------- VISIBILITY
        written_visible: bool = False,
        coding_visible: bool = False,
        database_visible: bool = False,
        ui_state: UIState = UIState.SETUP,
        # ---------------- COMPLETION / REPORT
        final_feedback: str = "",
        report_output: str = "",
        # ---------------- BUTTONS
        show_submit: bool = True,
        show_retry: bool = False,
        show_next: bool = False,
        next_label: str = "Next Question",
        show_submit_interactive: bool = False,
    ):
        self.state = state
        self.question_counter = question_counter
        self.feedback = feedback

        # NEW DISPLAY
        self.written_display = written_display
        self.coding_display = coding_display
        self.database_display = database_display

        # LEGACY
        self.written_text = written_text
        self.coding_text = coding_text
        self.database_text = database_text

        # VISIBILITY
        self.written_visible = written_visible
        self.coding_visible = coding_visible
        self.database_visible = database_visible

        self.ui_state = ui_state

        self.final_feedback = final_feedback
        self.report_output = report_output

        self.show_submit = show_submit
        self.show_retry = show_retry
        self.show_next = show_next
        self.next_label = next_label
        self.show_submit_interactive = show_submit_interactive

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
            # ---------------- RESET INPUT BOXES
            "",
            "",
            "",
        ]
