# app/ui/bindings/builders/ui_outputs_builder.py


class UIOutputsBuilder:
    def __init__(self, c):
        self.c = c

    def build(self):
        return [
            self.c.state,
            # SETUP INPUTS
            self.c.role_input,
            self.c.interview_type_input,
            self.c.company_input,
            self.c.language_input,
            self.c.start_button,
            self.c.page_title,
            # HEADER
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
            # LOADER
            self.c.global_loader,
        ]
