# app/ui/bindings/builders/ui_outputs_builder.py


class UIOutputsBuilder:
    def __init__(self, c):
        self.c = c

    def build(self):
        return [
            # STATE
            self.c.state,

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

            # SECTION VISIBILITY
            self.c.setup_section,
            self.c.interview_section,
            self.c.completion_section,
            self.c.report_section,

            # QUESTION TYPE VISIBILITY
            self.c.written_container,
            self.c.coding_container,
            self.c.database_container,

            # BUTTONS
            self.c.written_submit,
            self.c.retry_button,
            self.c.next_button,

            # EDITORS
            self.c.written_box,
            self.c.coding_box,
            self.c.database_box,

            # LOADER (SEMPRE ULTIMO)
            self.c.global_loader,
        ]
