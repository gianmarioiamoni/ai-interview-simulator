# app/ui/layout/ui_components.py

from dataclasses import dataclass


@dataclass
class UILayoutComponents:

    state: object

    role_input: object
    interview_type_input: object
    company_input: object
    language_input: object
    start_button: object
    page_title: object

    question_counter: object
    feedback_output: object

    written_display: object
    coding_display: object
    database_display: object

    written_box: object
    coding_box: object
    database_box: object

    submit_button: object
    retry_button: object
    next_button: object

    final_feedback: object
    report_output: object

    global_loader: object
