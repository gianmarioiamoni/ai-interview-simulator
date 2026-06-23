# app/ui/bindings/builders/ui_outputs_builder.py


class UIOutputsBuilder:
    def __init__(self, c):
        self.c = c

    def build(self):

        outputs = [
            # 0 STATE
            self.c.state,
            # 1-8 SETUP INPUTS
            self.c.role_input,
            self.c.role_custom_name_input,
            self.c.interview_type_input,
            self.c.seniority_input,
            self.c.interview_length_input,
            self.c.company_input,
            self.c.language_input,
            self.c.advanced_context_accordion,
            self.c.start_button,
            # 6 TITLE
            self.c.page_title,
            # 7-8 HEADER
            self.c.question_counter,
            self.c.feedback_output,
            # 9-11 DISPLAY
            self.c.written_display,
            self.c.coding_display,
            self.c.database_display,
            # 12-14 REPORT
            self.c.final_feedback,
            self.c.report_output,
            self.c.report_section,
            # 15-16 EXPORT BUTTONS
            self.c.pdf_button,
            self.c.json_button,
            # 15-17 BUTTONS
            self.c.submit_button,
            self.c.retry_button,
            self.c.next_button,
            # 18-20 EDITORS
            self.c.written_box,
            self.c.coding_box,
            self.c.database_box,
            # 21 LOADER
            self.c.global_loader,
        ]


        return outputs
