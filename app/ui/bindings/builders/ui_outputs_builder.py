# app/ui/bindings/builders/ui_outputs_builder.py


class UIOutputsBuilder:
    def __init__(self, c):
        self.c = c

    def build(self):
        return [
            # STATE
            self.c.state,
            # SETUP VISIBILITY
            self.c.setup_container,
            # HEADER / FEEDBACK
            self.c.question_counter,
            self.c.feedback_output,
            # DISPLAY
            self.c.written_display,
            self.c.coding_display,
            self.c.database_display,
            # REPORT
            self.c.final_feedback,
            self.c.report_output,
            # BUTTONS
            self.c.submit_button,
            self.c.retry_button,
            self.c.next_button,
            # EDITORS
            self.c.written_box,
            self.c.coding_box,
            self.c.database_box,
            # LOADER (ALWAYS LAST)
            self.c.global_loader,
        ]
