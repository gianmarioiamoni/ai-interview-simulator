# app/ui/bindings/builders/ui_outputs_builder.py


class UIOutputsBuilder:
    def __init__(self, c):
        self.c = c

    def build(self):

        outputs = [
            # 0 STATE
            self.c.state,
            # 3-7 SETUP INPUTS
            self.c.role_input,
            self.c.interview_type_input,
            self.c.company_input,
            self.c.language_input,
            self.c.start_button,
            # 8 TITLE
            self.c.page_title,
            # 9-10 HEADER
            self.c.question_counter,
            self.c.feedback_output,
            # 11-13 DISPLAY
            self.c.written_display,
            self.c.coding_display,
            self.c.database_display,
            # 14-15 REPORT
            self.c.final_feedback,
            self.c.report_output,
            # 16-18 BUTTONS
            self.c.submit_button,
            self.c.retry_button,
            self.c.next_button,
            # 19-21 EDITORS
            self.c.written_box,
            self.c.coding_box,
            self.c.database_box,
        ]

        print("=== OUTPUT ORDER ===")
        for i, c in enumerate(outputs):
            print(i, type(c), getattr(c, "_id", None))

        return outputs
