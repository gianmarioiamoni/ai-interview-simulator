# app/ui/bindings/builders/ui_outputs_builder.py


class UIOutputsBuilder:
    def __init__(self, c):
        self.c = c

    def build(self):
        return [
            self.c.state,
            self.c.question_counter,
            self.c.feedback_output,
            self.c.written_display,
            self.c.coding_display,
            self.c.database_display,
            self.c.written_container,
            self.c.coding_container,
            self.c.database_container,
            self.c.setup_section,
            self.c.interview_section,
            self.c.completion_section,
            self.c.report_section,
            self.c.final_feedback,
            self.c.report_output,
            self.c.written_submit,
            self.c.retry_button,
            self.c.next_button,
            self.c.written_box,
            self.c.coding_box,
            self.c.database_box,
            self.c.start_loading_text,
        ]
