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
        written_text: str = "",
        coding_text: str = "",
        database_text: str = "",
        written_visible: bool = False,
        coding_visible: bool = False,
        database_visible: bool = False,
        ui_state: UIState = UIState.SETUP,
        final_feedback: str = "",
        show_submit: bool = True,
        show_retry: bool = False,
        show_next: bool = False,
        next_label: str = "Next Question",
        show_submit_interactive: bool = False,
    ):
        self.state = state
        self.question_counter = question_counter
        self.feedback = feedback
        self.written_text = written_text
        self.coding_text = coding_text
        self.database_text = database_text
        self.written_visible = written_visible
        self.coding_visible = coding_visible
        self.database_visible = database_visible
        self.ui_state = ui_state
        self.final_feedback = final_feedback
        self.show_submit = show_submit
        self.show_retry = show_retry
        self.show_next = show_next
        self.next_label = next_label
        self.show_submit_interactive = show_submit_interactive

    def to_gradio_outputs(self) -> List[Any]:
        # Build the exact output list expected by app.py

        setup_update, interview_update, completion_update, report_update = route_ui(
            self.ui_state
        )

        return [
            self.state,
            self.question_counter,
            self.feedback,
            self.written_text,
            self.coding_text,
            self.database_text,
            gr.update(visible=self.written_visible),
            gr.update(visible=self.coding_visible),
            gr.update(visible=self.database_visible),
            setup_update,
            interview_update,
            completion_update,
            report_update,
            self.final_feedback,
            gr.update(visible=self.show_submit, interactive=self.show_submit_interactive),
            gr.update(visible=self.show_retry),
            gr.update(visible=self.show_next, value=self.next_label),
        ]
